from __future__ import annotations

import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.artifacts.sales import SalesArtifactStore
from app.analytics.explain.sales import SalesExplanationBuilder
from app.analytics.features.sales import SalesFeatureBuilder
from app.analytics.kpi_registry import SALES_KPI_BY_FEATURE_NAME, sales_kpi_feature_name, SALES_KPI_REGISTRY
from app.analytics.prediction.sales import SalesPredictionService
from app.analytics.training.sales import SalesStackingTrainer
from app.db.models.data_upload import DataUpload
from app.db.models.employee import Employee
from app.db.models.user import User
from app.schemas.analytics import (
    SalesBulkPredictionResponse,
    SalesDatasetEmployeeResponse,
    SalesDatasetResponse,
    SalesEmployeePerformanceResponse,
    SalesKPIMetric,
    SalesModelStateResponse,
    SalesModelTrainResponse,
    SalesPredictionResponse,
    SalesWeeklyTrendPoint,
)


UPLOAD_DIR = Path("uploads")


def _row_employee_id(row: dict[str, Any]) -> Any:
    """Case-insensitive lookup for employee_id column (handles Employee_ID, employee_id, etc.)."""
    for key in ("employee_id", "Employee_ID", "Employee_Id", "EMPLOYEE_ID"):
        if key in row and row[key] not in (None, ""):
            return row[key]
    # Fallback: scan all keys
    for key, val in row.items():
        if key.lower() == "employee_id" and val not in (None, ""):
            return val
    return None


def _row_get(row: dict[str, Any], col: str) -> Any:
    """Case-insensitive column getter."""
    if col in row:
        return row[col]
    col_lower = col.lower()
    for key, val in row.items():
        if key.lower() == col_lower:
            return val
    return None


SUPPORTED_TARGETS = {
    "Performance_Drop_Target",
    "Burnout_Target",
    "Resignation_Target",
    "High_Risk_Target",
}
TARGET_LABELS = {
    "Performance_Drop_Target": "Performans Dususu",
    "Burnout_Target": "Tukenmislik",
    "Resignation_Target": "Istifa Riski",
    "High_Risk_Target": "Yuksek Risk",
}
logger = logging.getLogger(__name__)


class SalesMLService:
    @staticmethod
    def _risk_rank(predicted_band: str) -> int:
        return {"Yuksek": 3, "1": 3, "Evet": 3, "Orta": 2, "Dusuk": 1, "0": 1, "Hayir": 1}.get(str(predicted_band), 2)

    @staticmethod
    def _risk_bucket(predicted_band: str) -> str:
        rank = SalesMLService._risk_rank(predicted_band)
        if rank >= 3:
            return "high"
        if rank == 2:
            return "medium"
        return "low"

    @staticmethod
    def _prediction_response(
        upload_id: int,
        employee_id: int,
        prediction: Any,
        *,
        employee_profile: dict[str, Any] | None = None,
        allow_llm_narrative: bool = False,
    ) -> SalesPredictionResponse:
        summary_payload = dict(prediction.summary_payload)
        if employee_profile:
            for k, v in employee_profile.items():
                if v is not None or k not in summary_payload:
                    summary_payload[k] = v

        response = SalesPredictionResponse(
            department=prediction.department,
            upload_id=upload_id,
            employee_id=employee_id,
            target_column=prediction.target_column,
            predicted_band=prediction.predicted_band,
            confidence=prediction.confidence,
            probabilities=prediction.probabilities,
            top_features=prediction.top_features,
            risk_summary=prediction.risk_summary,
            top_drivers=prediction.top_drivers,
            recommended_actions=prediction.recommended_actions,
            summary_payload=summary_payload,
        )
        from app.services.sales_narrative_service import SalesNarrativeService

        response.narrative = SalesNarrativeService.build(response, allow_llm=allow_llm_narrative)
        return response

    @staticmethod
    def _dataset_employee_code(employee_id: int) -> str:
        return f"SA-{employee_id:03d}"

    @staticmethod
    def _normalize_employee_key(value: Any) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.upper().startswith("SA-"):
            try:
                return str(int(text.split("-", 1)[1]))
            except ValueError:
                return text.upper()
        try:
            return str(int(float(text)))
        except ValueError:
            return text

    @staticmethod
    def _employee_profile(db: Session, employee_id: int, row: dict[str, Any] | None = None) -> dict[str, Any]:
        # Try DB primary key first (handles calls from get_my_performance where employee.id is passed)
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            candidate_codes = {SalesMLService._dataset_employee_code(employee_id), str(employee_id)}
            employee = (
                db.query(Employee)
                .filter(Employee.external_employee_code.in_(candidate_codes))
                .first()
            )

        team = _row_get(row or {}, "team") or _row_get(row or {}, "region") or _row_get(row or {}, "department")
        role = _row_get(row or {}, "role") or _row_get(row or {}, "role_level")
        if employee:
            display_name = employee.full_name or f"Calisan {employee.external_employee_code or employee_id}"
            position = employee.position or role
            return {
                "employee_name": display_name,
                "display_label": f"{display_name} - {employee.team or team or 'Takim yok'} / {position or 'Pozisyon yok'}",
                "position": position,
                "external_employee_code": employee.external_employee_code,
                "db_employee_id": employee.id,
                "team": employee.team or team,
                "role": role,
            }

        fallback_label = f"{team or 'Takim yok'} / {role or 'Rol yok'} - Dataset #{employee_id}"
        return {
            "employee_name": None,
            "display_label": fallback_label,
            "position": role,
            "external_employee_code": SalesMLService._dataset_employee_code(employee_id),
            "db_employee_id": None,
            "team": team,
            "role": role,
        }

    @staticmethod
    def list_datasets(db: Session) -> list[SalesDatasetResponse]:
        uploads = (
            db.query(DataUpload)
            .filter(
                DataUpload.file_type == "Performans Metrikleri (KPI)",
                DataUpload.status == "Success",
            )
            .order_by(DataUpload.upload_date.desc())
            .limit(100)
            .all()
        )
        sales_uploads = [
            upload
            for upload in uploads
            if SalesMLService._is_sales_upload(upload)
        ]
        return [
            SalesDatasetResponse(
                id=upload.id,
                file_name=upload.file_name,
                file_type=upload.file_type,
                status=upload.status,
                record_count=upload.record_count or 0,
                upload_date=upload.upload_date.isoformat() if upload.upload_date else "",
                raw_info=upload.raw_info,
            )
            for upload in sales_uploads
        ]

    @staticmethod
    def list_dataset_employees(db: Session, upload_id: int) -> list[SalesDatasetEmployeeResponse]:
        upload = SalesMLService._resolve_upload(db, upload_id)
        rows = SalesMLService._load_rows(SalesMLService._upload_path(upload))

        employees: dict[int, dict[str, Any]] = {}
        for row in rows:
            raw_employee_id = _row_employee_id(row)
            if raw_employee_id in (None, ""):
                continue
            from app.analytics.features.sales import _parse_employee_id_raw
            employee_id = _parse_employee_id_raw(raw_employee_id)
            if employee_id is None:
                continue

            if employee_id not in employees:
                profile = SalesMLService._employee_profile(db, employee_id, row)
                employees[employee_id] = {
                    "employee_id": employee_id,
                    "employee_name": profile.get("employee_name"),
                    "display_label": profile.get("display_label"),
                    "external_employee_code": profile.get("external_employee_code"),
                    "team": _row_get(row, "team") or _row_get(row, "region"),
                    "role": _row_get(row, "role") or _row_get(row, "role_level"),
                    "position": profile.get("position"),
                    "row_count": 0,
                }
            employees[employee_id]["row_count"] += 1

        return [
            SalesDatasetEmployeeResponse(**emp)
            for emp in sorted(employees.values(), key=lambda item: item["employee_id"])
        ]

    @staticmethod
    def list_model_states(db: Session, upload_id: int) -> list[SalesModelStateResponse]:
        SalesMLService._resolve_upload(db, upload_id)
        store = SalesArtifactStore()
        states: list[SalesModelStateResponse] = []

        for target_column in sorted(SUPPORTED_TARGETS):
            artifact_dir = store.root_dir / target_column
            metadata: dict[str, Any] = {}
            try:
                metadata = store.latest_metadata(target_column)
                if metadata.get("run_id"):
                    artifact_dir = artifact_dir / "runs" / str(metadata["run_id"])
            except (FileNotFoundError, json.JSONDecodeError):
                metadata = {}

            artifact_upload_id = metadata.get("upload_id")
            states.append(
                SalesModelStateResponse(
                    department="sales",
                    upload_id=upload_id,
                    target_column=target_column,
                    target_label=TARGET_LABELS.get(target_column, target_column),
                    is_trained=bool(metadata),
                    is_current_dataset=artifact_upload_id == upload_id if artifact_upload_id is not None else False,
                    trained_at=metadata.get("trained_at"),
                    model_name=metadata.get("model_name"),
                    train_count=metadata.get("train_count"),
                    test_count=metadata.get("test_count"),
                    labels=metadata.get("labels") or [],
                    metrics=metadata.get("metrics") or {},
                    artifact_dir=str(artifact_dir) if metadata else None,
                )
            )

        return states

    @staticmethod
    def _resolve_upload(db: Session, upload_id: int) -> DataUpload:
        upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Yukleme kaydi bulunamadi.")
        if upload.status != "Success":
            raise HTTPException(status_code=400, detail="Sadece basarili yuklemeler ML egitiminde kullanilabilir.")

        if not SalesMLService._is_sales_upload(upload):
            raise HTTPException(status_code=400, detail="Bu endpoint yalnizca sales upload'lari icindir.")

        return upload

    @staticmethod
    def _upload_path(upload: DataUpload) -> Path:
        path = UPLOAD_DIR / f"{upload.id}_{upload.file_name}"
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Yuklenen dosya bulunamadi: {path}")
        return path

    @staticmethod
    def _upload_headers(upload: DataUpload) -> set[str]:
        path = SalesMLService._upload_path(upload)
        ext = path.suffix.lower()
        if ext == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as file:
                return {str(header) for header in (csv.DictReader(file).fieldnames or [])}
        if ext == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                return {str(header) for header in payload[0].keys()}
            return set()
        if ext in {".xlsx", ".xls"}:
            try:
                import pandas as pd
            except ImportError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="XLSX okuma icin pandas backend ortaminda kurulu olmali.",
                ) from exc
            dataframe = pd.read_excel(path, nrows=0)
            return {str(header) for header in dataframe.columns}
        return set()

    @staticmethod
    def _is_sales_upload(upload: DataUpload) -> bool:
        if (upload.raw_info or {}).get("department_key") != "sales":
            return False
        try:
            headers = {header.lower() for header in SalesMLService._upload_headers(upload)}
        except HTTPException:
            return False
        return bool(headers & {target.lower() for target in SUPPORTED_TARGETS})

    @staticmethod
    def _load_rows(path: Path) -> list[dict[str, Any]]:
        ext = path.suffix.lower()
        if ext == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as file:
                return [dict(row) for row in csv.DictReader(file)]

        if ext == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return [payload]
            raise HTTPException(status_code=400, detail="JSON icerigi liste veya nesne formatinda olmali.")

        if ext == ".xlsx":
            try:
                import pandas as pd
            except ImportError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="XLSX okuma icin pandas backend ortaminda kurulu olmali.",
                ) from exc
            dataframe = pd.read_excel(path)
            dataframe = dataframe.where(dataframe.notna(), None)
            return dataframe.to_dict(orient="records")

        raise HTTPException(
            status_code=400,
            detail="ML egitimi icin CSV, XLSX veya JSON upload destekleniyor.",
        )

    @staticmethod
    def _candidate_employee_ids(db: Session, employee_id: int) -> set[str]:
        candidate_ids = {str(employee_id)}
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if employee and employee.external_employee_code:
            candidate_ids.add(employee.external_employee_code)
            if employee.external_employee_code.upper().startswith("SA-"):
                numeric_part = employee.external_employee_code.split("-", 1)[1]
                try:
                    candidate_ids.add(str(int(numeric_part)))
                except ValueError:
                    pass
        normalized_ids = {
            normalized
            for candidate in candidate_ids
            if (normalized := SalesMLService._normalize_employee_key(candidate))
        }
        return candidate_ids | normalized_ids

    @staticmethod
    def train_from_upload(
        db: Session,
        upload_id: int,
        target_column: str,
        test_period_count: int,
    ) -> SalesModelTrainResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")
        if test_period_count < 1:
            raise HTTPException(status_code=400, detail="test_period_count en az 1 olmali.")

        upload = SalesMLService._resolve_upload(db, upload_id)
        start = time.perf_counter()
        rows = SalesMLService._load_rows(SalesMLService._upload_path(upload))

        try:
            result = SalesStackingTrainer.train(
                rows,
                target_column=target_column,
                test_period_count=test_period_count,
            )
            artifact = SalesArtifactStore().save_training_result(result, upload_id=upload_id)
            logger.info(
                "sales_model_train_ok",
                extra={
                    "upload_id": upload_id,
                    "target_column": target_column,
                    "latency_ms": round((time.perf_counter() - start) * 1000),
                },
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return SalesModelTrainResponse(
            department="sales",
            upload_id=upload_id,
            target_column=result.target_column,
            model_name=result.model_name,
            train_count=result.train_count,
            test_count=result.test_count,
            labels=result.labels,
            metrics=result.metrics,
            top_features=result.top_features,
            validation_summary=result.validation_summary,
            artifact_dir=str(artifact.artifact_dir),
        )

    @staticmethod
    def predict_latest_from_upload(
        db: Session,
        upload_id: int,
        employee_id: int,
        target_column: str,
        use_llm_narrative: bool = False,
    ) -> SalesPredictionResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")

        upload = SalesMLService._resolve_upload(db, upload_id)
        rows = SalesMLService._load_rows(SalesMLService._upload_path(upload))
        candidate_employee_ids = SalesMLService._candidate_employee_ids(db, employee_id)
        employee_rows = [
            row
            for row in rows
            if SalesMLService._normalize_employee_key(_row_employee_id(row)) in candidate_employee_ids
            or str(_row_employee_id(row)) in candidate_employee_ids
        ]
        if not employee_rows:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Upload icinde employee_id bulunamadi: {employee_id}. "
                    f"Denenen eslesmeler: {', '.join(sorted(candidate_employee_ids))}"
                ),
            )

        try:
            artifact = SalesArtifactStore().load(target_column)
            prediction = SalesPredictionService.predict_latest(artifact, employee_rows)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"{target_column} icin egitilmis sales model artifact'i bulunamadi.",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return SalesMLService._prediction_response(
            upload_id=upload_id,
            employee_id=employee_id,
            prediction=prediction,
            employee_profile=SalesMLService._employee_profile(db, employee_id, employee_rows[-1] if employee_rows else None),
            allow_llm_narrative=use_llm_narrative,
        )

    @staticmethod
    def predict_all_from_upload(
        db: Session,
        upload_id: int,
        target_column: str,
        use_llm_narrative: bool = False,
        llm_team: str | None = None,
    ) -> SalesBulkPredictionResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")

        upload = SalesMLService._resolve_upload(db, upload_id)
        start = time.perf_counter()
        timings_ms: dict[str, int] = {}

        stage_start = time.perf_counter()
        rows = SalesMLService._load_rows(SalesMLService._upload_path(upload))
        timings_ms["load_rows_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        grouped_rows: dict[int, list[dict[str, Any]]] = {}
        from app.analytics.features.sales import _parse_employee_id_raw
        for row in rows:
            raw_employee_id = _row_employee_id(row)
            if raw_employee_id in (None, ""):
                continue
            employee_id = _parse_employee_id_raw(raw_employee_id)
            if employee_id is None:
                continue
            grouped_rows.setdefault(employee_id, []).append(row)
        timings_ms["group_rows_ms"] = round((time.perf_counter() - stage_start) * 1000)

        if not grouped_rows:
            raise HTTPException(status_code=404, detail="Upload icinde tahmin icin employee_id bulunamadi.")

        stage_start = time.perf_counter()
        try:
            artifact = SalesArtifactStore().load(target_column)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"{target_column} icin egitilmis sales model artifact'i bulunamadi.",
            ) from exc
        timings_ms["load_artifact_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        items: list[SalesPredictionResponse] = []
        for employee_id, employee_rows in grouped_rows.items():
            try:
                prediction = SalesPredictionService.predict_latest(artifact, employee_rows)
            except ValueError:
                continue
            items.append(
                SalesMLService._prediction_response(
                    upload_id=upload_id,
                    employee_id=employee_id,
                    prediction=prediction,
                    employee_profile=SalesMLService._employee_profile(db, employee_id, employee_rows[-1] if employee_rows else None),
                    allow_llm_narrative=False,
                )
            )
        timings_ms["employee_predictions_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        items.sort(
            key=lambda item: (
                SalesMLService._risk_rank(item.predicted_band),
                item.confidence,
            ),
            reverse=True,
        )

        high_risk_count = sum(1 for item in items if SalesMLService._risk_bucket(item.predicted_band) == "high")
        medium_risk_count = sum(1 for item in items if SalesMLService._risk_bucket(item.predicted_band) == "medium")
        low_risk_count = sum(1 for item in items if SalesMLService._risk_bucket(item.predicted_band) == "low")
        top_reasons = SalesMLService._top_driver_counts(items)
        team_summaries = SalesMLService._team_summaries(items)
        timings_ms["summaries_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        team_analytics = SalesMLService._team_analytics(rows, artifact, target_column)
        timings_ms["team_analytics_ms"] = round((time.perf_counter() - stage_start) * 1000)

        from app.services.sales_narrative_service import SalesNarrativeService

        stage_start = time.perf_counter()
        department_narrative = SalesNarrativeService.build_department_narrative(
            target_column=target_column,
            prediction_count=len(items),
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            top_reasons=top_reasons,
            team_summaries=team_summaries,
            allow_llm=use_llm_narrative and not llm_team,
        )
        team_narratives = SalesNarrativeService.build_team_narratives(
            target_column=target_column,
            team_summaries=team_summaries,
            allow_llm=use_llm_narrative,
            llm_team=llm_team,
        )
        timings_ms["narratives_ms"] = round((time.perf_counter() - stage_start) * 1000)
        timings_ms["total_ms"] = round((time.perf_counter() - start) * 1000)

        logger.info(
            "sales_bulk_predict_timing %s",
            json.dumps(
                {
                    "upload_id": upload_id,
                    "target_column": target_column,
                    "prediction_count": len(items),
                    **timings_ms,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

        return SalesBulkPredictionResponse(
            department="sales",
            upload_id=upload_id,
            target_column=target_column,
            prediction_count=len(items),
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            generated_at=datetime.now(timezone.utc),
            department_narrative=department_narrative,
            team_narratives=team_narratives,
            team_analytics=team_analytics,
            items=items,
        )

    @staticmethod
    def _top_driver_counts(items: list[SalesPredictionResponse], limit: int = 5) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for item in items:
            driver_name = "KPI sinyali"
            if item.top_drivers:
                driver_name = str(item.top_drivers[0].get("metric_name") or driver_name)
            counts[driver_name] = counts.get(driver_name, 0) + 1
        return sorted(counts.items(), key=lambda entry: entry[1], reverse=True)[:limit]

    @staticmethod
    def _team_summaries(items: list[SalesPredictionResponse]) -> list[dict[str, Any]]:
        grouped: dict[str, list[SalesPredictionResponse]] = {}
        for item in items:
            team = str(item.summary_payload.get("team") or "Takim bilgisi yok")
            grouped.setdefault(team, []).append(item)

        summaries: list[dict[str, Any]] = []
        for team, team_items in grouped.items():
            high = sum(1 for item in team_items if SalesMLService._risk_bucket(item.predicted_band) == "high")
            medium = sum(1 for item in team_items if SalesMLService._risk_bucket(item.predicted_band) == "medium")
            low = sum(1 for item in team_items if SalesMLService._risk_bucket(item.predicted_band) == "low")
            top_reason_list = SalesMLService._top_driver_counts(team_items, limit=1)
            top_reason = top_reason_list[0][0] if top_reason_list else "KPI sinyali"
            role_counts: dict[str, int] = {}
            for item in team_items:
                role = str(item.summary_payload.get("position") or item.summary_payload.get("role") or "Rol yok")
                role_counts[role] = role_counts.get(role, 0) + 1
            summaries.append(
                {
                    "team": team,
                    "total": len(team_items),
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "topReason": top_reason,
                    "role_counts": role_counts,
                }
            )
        return sorted(summaries, key=lambda item: (item["high"], item["medium"], item["total"]), reverse=True)

    @staticmethod
    def _probability_risk_score(probabilities: dict[str, float], predicted_band: str | None = None) -> int:
        score = (
            probabilities.get("Yuksek", 0.0) * 100
            + probabilities.get("1", 0.0) * 100
            + probabilities.get("Evet", 0.0) * 100
            + probabilities.get("Orta", 0.0) * 55
            + probabilities.get("Dusuk", 0.0) * 15
            + probabilities.get("0", 0.0) * 10
        )
        if not probabilities and predicted_band:
            score = {"Yuksek": 85, "1": 85, "Evet": 85, "Orta": 55, "Dusuk": 20, "0": 20, "Hayir": 20}.get(predicted_band, 50)
        return int(round(score))

    @staticmethod
    def _team_analytics(rows: list[dict[str, Any]], artifact: Any, target_column: str) -> list[dict[str, Any]]:
        dataset = SalesFeatureBuilder.build_from_rows(rows)
        if not dataset.feature_rows:
            return []

        classifier = artifact.pipeline.named_steps.get("classifier")
        classes = [str(label) for label in getattr(classifier, "classes_", [])]
        predictions = [str(label) for label in artifact.pipeline.predict(dataset.feature_rows)]
        probability_rows = (
            artifact.pipeline.predict_proba(dataset.feature_rows)
            if hasattr(artifact.pipeline, "predict_proba")
            else []
        )
        period_scores: dict[str, dict[str, list[int]]] = {}

        for index, metadata in enumerate(dataset.metadata_rows):
            team = str(metadata.get("team") or "Takim bilgisi yok")
            period_date = str(metadata.get("period_date") or "")
            period = period_date[:7] if period_date else ""
            predicted_band = predictions[index]
            probabilities: dict[str, float] = {}
            if len(probability_rows):
                probability_values = probability_rows[index]
                probabilities = {
                    label: round(float(probability), 6)
                    for label, probability in zip(classes, probability_values)
                }
            score = SalesMLService._probability_risk_score(probabilities, predicted_band)
            period_scores.setdefault(team, {}).setdefault(period, []).append(score)

        analytics: list[dict[str, Any]] = []
        for team, periods in period_scores.items():
            ordered_periods = sorted(period for period in periods if period)[-6:]
            trend_values = [
                int(round(sum(periods[period]) / len(periods[period])))
                for period in ordered_periods
                if periods[period]
            ]
            latest_score = trend_values[-1] if trend_values else 0
            analytics.append(
                {
                    "team": team,
                    "risk_score": latest_score,
                    "trend_values": trend_values,
                    "trend_periods": ordered_periods,
                    "trend_basis": "model_probability_by_period",
                }
            )

        return sorted(analytics, key=lambda item: item["risk_score"], reverse=True)

    # ------------------------------------------------------------------
    # Satış çalışanı kişisel performans dashboard verisi
    # ------------------------------------------------------------------

    # Dashboard'da gösterilecek 9 KPI: (short_code, feature_name, unit_type)
    # unit_type: "ratio" → 0-1, "days" → sayı, "score_5" → 0-5, "score_10" → 0-10
    _DASHBOARD_KPIS: list[tuple[str, str, str]] = [
        ("SHGO", "kpi_1_shgo", "ratio"),
        ("LMDO", "kpi_4_lmdo", "ratio"),
        ("TKO", "kpi_5_tko", "ratio"),
        ("OSDS", "kpi_6_osds", "days"),
        ("CSAT", "kpi_15_csat", "score_5"),
        ("CRMD", "kpi_17_crmd", "ratio"),
        ("TDO", "kpi_14_tdo", "ratio"),
        ("PSO", "kpi_10_pso", "ratio"),
        ("MS", "kpi_19_ms", "score_5"),
    ]

    @staticmethod
    def _composite_weekly_score(feature_row: dict[str, Any]) -> float:
        scores: list[float] = []
        for code, fname, unit_type in SalesMLService._DASHBOARD_KPIS:
            v = feature_row.get(fname)
            if v is None:
                continue
            v = float(v)
            if unit_type == "ratio":
                scores.append(min(v * 100, 100.0))
            elif unit_type == "days":
                # lower_is_better: 0 days → 100, 90+ days → 0
                scores.append(max(0.0, 100.0 - v / 90.0 * 100.0))
            elif unit_type in ("score_5", "score_10"):
                scale = 5.0 if unit_type == "score_5" else 10.0
                scores.append(min(v / scale * 100.0, 100.0))
        return round(sum(scores) / len(scores), 1) if scores else 50.0

    @staticmethod
    def _kpi_metrics_from_feature_row(feature_row: dict[str, Any]) -> dict[str, SalesKPIMetric]:
        kpis: dict[str, SalesKPIMetric] = {}
        for code, fname, unit_type in SalesMLService._DASHBOARD_KPIS:
            definition = SALES_KPI_BY_FEATURE_NAME.get(fname)
            raw_value = feature_row.get(fname)
            if raw_value is not None:
                raw_value = float(raw_value)

            threshold_status: str | None = None
            trend_signal: str | None = None
            if definition and raw_value is not None:
                threshold_status = SalesExplanationBuilder._threshold_status(definition, raw_value)
                trend_raw = feature_row.get(f"{fname}_trend_4")
                trend_signal = SalesExplanationBuilder._trend_signal(definition, trend_raw)

            kpis[code] = SalesKPIMetric(
                code=code,
                name=definition.display_name if definition else code,
                raw_value=raw_value,
                unit=unit_type,
                direction=definition.direction if definition else "higher_is_better",
                threshold_status=threshold_status,
                trend_signal=trend_signal,
            )
        return kpis

    @staticmethod
    def get_my_performance(db: Session, current_user: User) -> SalesEmployeePerformanceResponse:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı.")

        # En son satış upload'ını bul
        uploads = (
            db.query(DataUpload)
            .filter(DataUpload.file_type == "Performans Metrikleri (KPI)", DataUpload.status == "Success")
            .order_by(DataUpload.upload_date.desc())
            .limit(20)
            .all()
        )
        sales_uploads = [u for u in uploads if (u.raw_info or {}).get("department_key") == "sales"]
        if not sales_uploads:
            return SalesEmployeePerformanceResponse(
                employee_id=employee.id,
                external_code=employee.external_employee_code,
                has_upload=False,
            )

        upload = sales_uploads[0]
        rows = SalesMLService._load_rows(SalesMLService._upload_path(upload))

        # Bu çalışana ait satırları filtrele
        candidate_ids = SalesMLService._candidate_employee_ids(db, employee.id)
        from app.analytics.features.sales import _parse_employee_id_raw
        employee_rows = [
            row for row in rows
            if SalesMLService._normalize_employee_key(_row_employee_id(row)) in candidate_ids
            or str(_row_employee_id(row)) in candidate_ids
        ]
        if not employee_rows:
            return SalesEmployeePerformanceResponse(
                employee_id=employee.id,
                external_code=employee.external_employee_code,
                has_upload=True,
            )

        dataset = SalesFeatureBuilder.build_from_rows(employee_rows)
        if not dataset.feature_rows:
            return SalesEmployeePerformanceResponse(
                employee_id=employee.id,
                external_code=employee.external_employee_code,
                has_upload=True,
            )

        # En son haftayı bul
        latest_index = max(
            range(len(dataset.metadata_rows)),
            key=lambda i: (dataset.metadata_rows[i]["year"], dataset.metadata_rows[i]["week"]),
        )
        latest_feature_row = dataset.feature_rows[latest_index]
        latest_meta = dataset.metadata_rows[latest_index]
        latest_period = f"{latest_meta['year']}-W{latest_meta['week']:02d}"

        # KPI metrikleri
        kpis = SalesMLService._kpi_metrics_from_feature_row(latest_feature_row)

        # Haftalık trend (son 8 hafta)
        sorted_pairs = sorted(
            zip(dataset.feature_rows, dataset.metadata_rows),
            key=lambda p: (p[1]["year"], p[1]["week"]),
        )
        trend_window = list(sorted_pairs)[-8:]
        weekly_trend = [
            SalesWeeklyTrendPoint(
                label=f"H{i + 1}",
                score=SalesMLService._composite_weekly_score(fr),
            )
            for i, (fr, _meta) in enumerate(trend_window)
        ]

        # ML tahmini (Performance_Drop_Target)
        prediction: SalesPredictionResponse | None = None
        has_model = False
        try:
            artifact = SalesArtifactStore().load("Performance_Drop_Target")
            pred = SalesPredictionService.predict_latest(artifact, employee_rows)
            prediction = SalesMLService._prediction_response(
                upload_id=upload.id,
                employee_id=employee.id,
                prediction=pred,
                employee_profile=SalesMLService._employee_profile(db, employee.id, employee_rows[-1]),
                allow_llm_narrative=False,
            )
            has_model = True
        except (FileNotFoundError, ValueError):
            pass

        return SalesEmployeePerformanceResponse(
            employee_id=employee.id,
            external_code=employee.external_employee_code,
            latest_period=latest_period,
            kpis=kpis,
            weekly_trend=weekly_trend,
            prediction=prediction,
            has_upload=True,
            has_model=has_model,
        )
