from __future__ import annotations

import csv
import json
import logging
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.artifacts.software import SoftwareArtifactStore
from app.analytics.explain.software import SoftwareExplanationBuilder
from app.analytics.features.software import SoftwareFeatureBuilder
from app.analytics.kpi_registry import KPIDefinition, SOFTWARE_KPI_BY_CODE, software_kpi_feature_name
from app.analytics.prediction.software import SoftwarePredictionService
from app.analytics.training.software import SoftwareBaselineTrainer
from app.db.models.data_upload import DataUpload
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.nlp import FeedbackNLPAnalysis, NLPSourceType, RiskLevel
from app.db.models.survey_response import SurveyResponse
from app.db.models.user import User, UserRole
from app.schemas.analytics import (
    DepartmentDashboardAISummaryResponse,
    DepartmentDashboardActionResponse,
    DepartmentDashboardActionsResponse,
    DepartmentDashboardCoverageResponse,
    DepartmentDashboardDepartmentResponse,
    DepartmentDashboardInsightResponse,
    DepartmentDashboardScoresResponse,
    DepartmentDashboardSourceResponse,
    DepartmentDashboardTeamResponse,
    SoftwareBulkPredictionResponse,
    SoftwareDepartmentDashboardResponse,
    SoftwareDatasetEmployeeResponse,
    SoftwareDatasetResponse,
    SoftwareDepartmentInsightsResponse,
    SoftwareEmployeeKPIMetricResponse,
    SoftwareEmployeePerformanceResponse,
    SoftwareModelStateResponse,
    SoftwareModelTrainResponse,
    SoftwarePredictionResponse,
)


UPLOAD_DIR = Path("uploads")
SUPPORTED_TARGETS = {
    "performance_band",
    "attrition_risk_band",
    "Performance_Drop_Target",
    "Burnout_Target",
    "Resignation_Target",
    "High_Risk_Target",
}
SUPPORTED_MODELS = {
    "logistic_regression",
    "random_forest",
    "hist_gradient_boosting",
    "stacking_lgbm_xgb_rf_lr",
}
TARGET_LABELS = {
    "performance_band":        "Performans",
    "attrition_risk_band":     "Ayrilma Riski",
    "Performance_Drop_Target": "Performans Dususu",
    "Burnout_Target":          "Tukenmislik",
    "Resignation_Target":      "Istifa Riski",
    "High_Risk_Target":        "Yuksek Risk",
}
# Yeni dataset'te kullanılan 4 binary hedef
SW_BINARY_TARGETS = (
    "Performance_Drop_Target",
    "Burnout_Target",
    "Resignation_Target",
    "High_Risk_Target",
)
EMPLOYEE_DASHBOARD_KPIS = tuple(f"KPI-{index}" for index in range(1, 21))
logger = logging.getLogger(__name__)


class SoftwareMLService:
    @staticmethod
    def _risk_rank(target_column: str, predicted_band: str) -> int:
        if target_column == "attrition_risk_band":
            return {"Yuksek": 3, "Orta": 2, "Dusuk": 1}.get(predicted_band, 0)
        return {"Riskli": 3, "Stabil": 2, "Yuksek": 1, "Guclu": 1}.get(predicted_band, 0)

    @staticmethod
    def _risk_bucket(target_column: str, predicted_band: str) -> str:
        rank = SoftwareMLService._risk_rank(target_column, predicted_band)
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
    ) -> SoftwarePredictionResponse:
        summary_payload = dict(prediction.summary_payload)
        if employee_profile:
            summary_payload.update(employee_profile)

        response = SoftwarePredictionResponse(
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
        from app.services.software_narrative_service import SoftwareNarrativeService

        response.narrative = SoftwareNarrativeService.build(
            response,
            allow_llm=allow_llm_narrative,
        )
        return response

    @staticmethod
    def _dataset_employee_code(employee_id: int) -> str:
        return f"SE-{employee_id:03d}"

    @staticmethod
    def _normalize_employee_key(value: Any) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.upper().startswith("SE-"):
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
        candidate_codes = {SoftwareMLService._dataset_employee_code(employee_id), str(employee_id)}
        employee = (
            db.query(Employee)
            .filter(Employee.external_employee_code.in_(candidate_codes))
            .first()
        )

        team = (row or {}).get("team")
        role = (row or {}).get("role")
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
            "external_employee_code": SoftwareMLService._dataset_employee_code(employee_id),
            "db_employee_id": None,
            "team": team,
            "role": role,
        }

    @staticmethod
    def list_datasets(db: Session) -> list[SoftwareDatasetResponse]:
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

        software_uploads = [
            upload
            for upload in uploads
            if SoftwareMLService._is_software_upload(upload)
        ]

        return [
            SoftwareDatasetResponse(
                id=upload.id,
                file_name=upload.file_name,
                file_type=upload.file_type,
                status=upload.status,
                record_count=upload.record_count or 0,
                upload_date=upload.upload_date.isoformat() if upload.upload_date else "",
                raw_info=upload.raw_info,
            )
            for upload in software_uploads
        ]

    @staticmethod
    def list_dataset_employees(db: Session, upload_id: int) -> list[SoftwareDatasetEmployeeResponse]:
        upload = SoftwareMLService._resolve_upload(db, upload_id)
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))

        import re as _re2
        employees: dict[int, dict[str, Any]] = {}
        for row in rows:
            raw_employee_id = row.get("employee_id")
            if raw_employee_id in (None, ""):
                continue
            try:
                employee_id = int(float(raw_employee_id))
            except (TypeError, ValueError):
                digits = _re2.sub(r"[^0-9]", "", str(raw_employee_id))
                if not digits:
                    continue
                employee_id = int(digits)

            if employee_id not in employees:
                profile = SoftwareMLService._employee_profile(db, employee_id, row)
                employees[employee_id] = {
                    "employee_id": employee_id,
                    "employee_name": profile.get("employee_name"),
                    "display_label": profile.get("display_label"),
                    "external_employee_code": profile.get("external_employee_code"),
                    "team": row.get("team"),
                    "role": row.get("role"),
                    "position": profile.get("position"),
                    "row_count": 0,
                }
            employees[employee_id]["row_count"] += 1

        return [
            SoftwareDatasetEmployeeResponse(**employee)
            for employee in sorted(employees.values(), key=lambda item: item["employee_id"])
        ]

    @staticmethod
    def list_model_states(db: Session, upload_id: int) -> list[SoftwareModelStateResponse]:
        SoftwareMLService._resolve_upload(db, upload_id)
        store = SoftwareArtifactStore()
        states: list[SoftwareModelStateResponse] = []

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
                SoftwareModelStateResponse(
                    department="software",
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
    def get_my_performance(db: Session, current_user: User) -> SoftwareEmployeePerformanceResponse:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Giris yapan kullanici icin calisan kaydi bulunamadi.")

        upload = SoftwareMLService._latest_successful_upload(db)
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))
        candidate_employee_ids = SoftwareMLService._candidate_employee_ids(db, employee.id)
        employee_rows = [
            row
            for row in rows
            if SoftwareMLService._normalize_employee_key(row.get("employee_id")) in candidate_employee_ids
            or str(row.get("employee_id")) in candidate_employee_ids
        ]
        if not employee_rows:
            raise HTTPException(
                status_code=404,
                detail=(
                    "En son software dataset'i icinde bu calisana ait KPI satiri bulunamadi. "
                    f"Denenen eslesmeler: {', '.join(sorted(candidate_employee_ids))}"
                ),
            )

        dataset = SoftwareFeatureBuilder.build_from_rows(employee_rows)
        if not dataset.feature_rows:
            raise HTTPException(status_code=404, detail="Calisan KPI satirlari analiz edilebilir formatta degil.")

        latest_index = max(
            range(len(dataset.metadata_rows)),
            key=lambda index: (
                dataset.metadata_rows[index].get("year") or 0,
                dataset.metadata_rows[index].get("week") or 0,
            ),
        )
        latest_metadata = dataset.metadata_rows[latest_index]
        latest_feature_row = dataset.feature_rows[latest_index]
        latest_raw_row = SoftwareMLService._latest_raw_employee_row(employee_rows)
        metrics = SoftwareMLService._employee_dashboard_metrics(latest_feature_row, latest_raw_row)

        prediction: SoftwarePredictionResponse | None = None
        try:
            artifact = SoftwareArtifactStore().load("performance_band")
            raw_prediction = SoftwarePredictionService.predict_latest(artifact, employee_rows)
            prediction = SoftwareMLService._prediction_response(
                upload_id=upload.id,
                employee_id=employee.id,
                prediction=raw_prediction,
                employee_profile=SoftwareMLService._employee_profile(db, employee.id, employee_rows[-1]),
                allow_llm_narrative=False,
            )
        except (FileNotFoundError, ValueError):
            prediction = None

        trend_points = SoftwareMLService._performance_trend(dataset)
        return SoftwareEmployeePerformanceResponse(
            department="software",
            upload_id=upload.id,
            file_name=upload.file_name,
            employee_id=employee.id,
            employee_name=employee.full_name,
            team=employee.team or latest_metadata.get("team"),
            role=employee.position or latest_metadata.get("role"),
            period_label=f"{latest_metadata.get('year')}-W{int(latest_metadata.get('week') or 0):02d}",
            latest_period=latest_metadata.get("period_date"),
            metrics=metrics,
            trend_labels=[item["label"] for item in trend_points],
            trend_values=[item["value"] for item in trend_points],
            prediction=prediction,
        )

    @staticmethod
    def _resolve_upload(db: Session, upload_id: int) -> DataUpload:
        upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Yukleme kaydi bulunamadi.")
        if upload.status != "Success":
            raise HTTPException(status_code=400, detail="Sadece basarili yuklemeler ML egitiminde kullanilabilir.")

        if not SoftwareMLService._is_software_upload(upload):
            raise HTTPException(status_code=400, detail="Bu endpoint yalnizca software upload'lari icindir.")

        return upload

    @staticmethod
    def _latest_successful_upload(db: Session) -> DataUpload:
        uploads = (
            db.query(DataUpload)
            .filter(
                DataUpload.file_type == "Performans Metrikleri (KPI)",
                DataUpload.status == "Success",
            )
            .order_by(DataUpload.upload_date.desc())
            .limit(50)
            .all()
        )
        for upload in uploads:
            if SoftwareMLService._is_software_upload(upload):
                return upload
        raise HTTPException(status_code=404, detail="Basarili software KPI dataset'i bulunamadi.")

    @staticmethod
    def _employee_dashboard_metrics(
        feature_row: dict[str, Any],
        raw_row: dict[str, Any] | None = None,
    ) -> list[SoftwareEmployeeKPIMetricResponse]:
        metrics: list[SoftwareEmployeeKPIMetricResponse] = []
        definitions = [
            definition
            for prefix in EMPLOYEE_DASHBOARD_KPIS
            for code, definition in SOFTWARE_KPI_BY_CODE.items()
            if code.startswith(f"{prefix} ")
        ]
        seen_codes: set[str] = set()
        for definition in definitions:
            if definition.canonical_code in seen_codes:
                continue
            seen_codes.add(definition.canonical_code)
            if not definition:
                continue
            feature_name = software_kpi_feature_name(definition)
            raw_value = feature_row.get(feature_name)
            if raw_value in (None, "") and raw_row:
                for column_name in definition.source_columns:
                    if column_name in raw_row and raw_row[column_name] not in (None, ""):
                        raw_value = raw_row[column_name]
                        break
            numeric_value = SoftwareFeatureBuilder._parse_float(raw_value)
            if numeric_value is None:
                continue
            if definition.unit == "ratio" and numeric_value > 1.5:
                numeric_value = round(numeric_value / 100, 6)
            status = SoftwareExplanationBuilder._threshold_status(definition, numeric_value)
            metrics.append(
                SoftwareEmployeeKPIMetricResponse(
                    code=definition.short_code,
                    label=definition.display_name,
                    value=SoftwareMLService._format_kpi_value(definition, numeric_value),
                    raw_value=round(numeric_value, 6),
                    unit=definition.unit,
                    status=SoftwareMLService._short_status(status),
                    tone=SoftwareMLService._tone_from_status(status),
                    bar_pct=SoftwareMLService._bar_pct(definition, numeric_value),
                    hint=SoftwareMLService._threshold_hint(definition),
                    category=definition.category,
                )
            )
        return metrics

    @staticmethod
    def _latest_raw_employee_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        return max(
            rows,
            key=lambda row: (
                SoftwareFeatureBuilder._parse_int(row.get("year")) or 0,
                SoftwareFeatureBuilder._parse_int(row.get("week")) or 0,
            ),
        )

    @staticmethod
    def _performance_trend(dataset: Any) -> list[dict[str, Any]]:
        trend: list[dict[str, Any]] = []
        gto_feature = software_kpi_feature_name(SOFTWARE_KPI_BY_CODE["KPI-1 GTO"])
        zto_feature = software_kpi_feature_name(SOFTWARE_KPI_BY_CODE["KPI-2 ZTO"])
        kke_feature = software_kpi_feature_name(SOFTWARE_KPI_BY_CODE["KPI-4 KKKE"])
        combined = sorted(
            zip(dataset.feature_rows, dataset.metadata_rows),
            key=lambda item: ((item[1].get("year") or 0), (item[1].get("week") or 0)),
        )[-6:]
        for feature_row, metadata in combined:
            values = [
                SoftwareFeatureBuilder._parse_float(feature_row.get(gto_feature)),
                SoftwareFeatureBuilder._parse_float(feature_row.get(zto_feature)),
                SoftwareFeatureBuilder._parse_float(feature_row.get(kke_feature)),
            ]
            present_values = [value for value in values if value is not None]
            if not present_values:
                continue
            score = round(sum(present_values) / len(present_values) * 100, 1)
            trend.append({"label": f"W{int(metadata.get('week') or 0):02d}", "value": score})
        return trend

    @staticmethod
    def _format_kpi_value(definition: KPIDefinition, value: float) -> str:
        if definition.unit == "ratio":
            return f"%{round(value * 100)}"
        if definition.unit == "bugs_per_kloc":
            return f"{value:.2f}"
        if definition.unit == "count":
            return f"{value:.1f}".rstrip("0").rstrip(".")
        if definition.unit in {"score", "index"}:
            if value <= 1.5:
                return f"%{round(value * 100)}"
            return f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _tone_from_status(status: str) -> str:
        if "Guclu" in status or "Optimal aralikta" in status:
            return "good"
        if "Risk" in status or "altinda" in status or "ustunde" in status:
            return "bad"
        return "warn"

    @staticmethod
    def _short_status(status: str) -> str:
        if "Guclu" in status or "Optimal aralikta" in status:
            return "Iyi"
        if "Risk" in status:
            return "Dikkat"
        return "Izle"

    @staticmethod
    def _bar_pct(definition: KPIDefinition, value: float) -> float:
        thresholds = definition.thresholds
        if definition.direction == "lower_is_better":
            target = thresholds.risk or thresholds.stable or max(value, 1.0)
            if target <= 0:
                return 1.0
            return max(0.04, min(value / target, 1.0))
        if definition.direction == "optimal_range":
            upper = thresholds.optimal_max or 1.0
            if upper <= 0:
                return 0.5
            return max(0.04, min(value / upper, 1.0))
        target = thresholds.strong or thresholds.stable or 1.0
        if target <= 0:
            return 0.0
        return max(0.04, min(value / target, 1.0))

    @staticmethod
    def _threshold_hint(definition: KPIDefinition) -> str:
        thresholds = definition.thresholds
        if definition.direction == "lower_is_better" and thresholds.strong is not None:
            return f"Hedef: {SoftwareMLService._format_kpi_value(definition, thresholds.strong)} alti"
        if definition.direction == "optimal_range":
            if thresholds.optimal_min is not None and thresholds.optimal_max is not None:
                return (
                    f"Hedef: {SoftwareMLService._format_kpi_value(definition, thresholds.optimal_min)} - "
                    f"{SoftwareMLService._format_kpi_value(definition, thresholds.optimal_max)}"
                )
            return "Hedef: dengeli aralik"
        if thresholds.strong is not None:
            return f"Hedef: {SoftwareMLService._format_kpi_value(definition, thresholds.strong)} uzeri"
        return "Hedef: takim standardi"

    @staticmethod
    def _upload_path(upload: DataUpload) -> Path:
        path = UPLOAD_DIR / f"{upload.id}_{upload.file_name}"
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Yuklenen dosya bulunamadi: {path}")
        return path

    @staticmethod
    def _upload_headers(upload: DataUpload) -> set[str]:
        path = SoftwareMLService._upload_path(upload)
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
    def _is_software_upload(upload: DataUpload) -> bool:
        if (upload.raw_info or {}).get("department_key") != "software":
            return False
        try:
            headers = {header.lower() for header in SoftwareMLService._upload_headers(upload)}
        except HTTPException:
            return False
        return bool(headers & SUPPORTED_TARGETS)

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
            if employee.external_employee_code.upper().startswith("SE-"):
                numeric_part = employee.external_employee_code.split("-", 1)[1]
                try:
                    candidate_ids.add(str(int(numeric_part)))
                except ValueError:
                    pass
        normalized_ids = {
            normalized
            for candidate in candidate_ids
            if (normalized := SoftwareMLService._normalize_employee_key(candidate))
        }
        return candidate_ids | normalized_ids

    @staticmethod
    def train_from_upload(
        db: Session,
        upload_id: int,
        target_column: str,
        model_name: str,
        test_period_count: int,
    ) -> SoftwareModelTrainResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")
        if model_name not in SUPPORTED_MODELS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen model_name: {model_name}")
        if test_period_count < 1:
            raise HTTPException(status_code=400, detail="test_period_count en az 1 olmali.")

        upload = SoftwareMLService._resolve_upload(db, upload_id)
        start = time.perf_counter()
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))

        try:
            result = SoftwareBaselineTrainer.train(
                rows,
                target_column=target_column,
                model_name=model_name,  # type: ignore[arg-type]
                test_period_count=test_period_count,
            )
            artifact = SoftwareArtifactStore().save_training_result(result, upload_id=upload_id)
            logger.info(
                "software_model_train_ok",
                extra={
                    "upload_id": upload_id,
                    "target_column": target_column,
                    "model_name": model_name,
                    "latency_ms": round((time.perf_counter() - start) * 1000),
                },
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return SoftwareModelTrainResponse(
            department="software",
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
    ) -> SoftwarePredictionResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")

        upload = SoftwareMLService._resolve_upload(db, upload_id)
        start = time.perf_counter()
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))
        candidate_employee_ids = SoftwareMLService._candidate_employee_ids(db, employee_id)
        employee_rows = [
            row
            for row in rows
            if SoftwareMLService._normalize_employee_key(row.get("employee_id")) in candidate_employee_ids
            or str(row.get("employee_id")) in candidate_employee_ids
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
            artifact = SoftwareArtifactStore().load(target_column)
            prediction = SoftwarePredictionService.predict_latest(artifact, employee_rows)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"{target_column} icin egitilmis software model artifact'i bulunamadi.",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return SoftwareMLService._prediction_response(
            upload_id=upload_id,
            employee_id=employee_id,
            prediction=prediction,
            employee_profile=SoftwareMLService._employee_profile(db, employee_id, employee_rows[-1] if employee_rows else None),
            allow_llm_narrative=use_llm_narrative,
        )

    @staticmethod
    def predict_all_from_upload(
        db: Session,
        upload_id: int,
        target_column: str,
        use_llm_narrative: bool = False,
        llm_team: str | None = None,
    ) -> SoftwareBulkPredictionResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")

        upload = SoftwareMLService._resolve_upload(db, upload_id)
        start = time.perf_counter()
        timings_ms: dict[str, int] = {}

        stage_start = time.perf_counter()
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))
        timings_ms["load_rows_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        grouped_rows: dict[int, list[dict[str, Any]]] = {}

        import re as _re
        for row in rows:
            raw_employee_id = row.get("employee_id")
            if raw_employee_id in (None, ""):
                continue
            try:
                employee_id = int(float(raw_employee_id))
            except (TypeError, ValueError):
                # SE-001, MGR-SW, vb. formatlar
                digits = _re.sub(r"[^0-9]", "", str(raw_employee_id))
                if not digits:
                    continue
                employee_id = int(digits)
            grouped_rows.setdefault(employee_id, []).append(row)
        timings_ms["group_rows_ms"] = round((time.perf_counter() - stage_start) * 1000)

        if not grouped_rows:
            raise HTTPException(status_code=404, detail="Upload icinde tahmin icin employee_id bulunamadi.")

        stage_start = time.perf_counter()
        try:
            artifact = SoftwareArtifactStore().load(target_column)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"{target_column} icin egitilmis software model artifact'i bulunamadi.",
            ) from exc
        timings_ms["load_artifact_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        items: list[SoftwarePredictionResponse] = []
        for employee_id, employee_rows in grouped_rows.items():
            try:
                prediction = SoftwarePredictionService.predict_latest(artifact, employee_rows)
            except ValueError:
                continue
            items.append(
                SoftwareMLService._prediction_response(
                    upload_id=upload_id,
                    employee_id=employee_id,
                    prediction=prediction,
                    employee_profile=SoftwareMLService._employee_profile(db, employee_id, employee_rows[-1] if employee_rows else None),
                    allow_llm_narrative=False,
                )
            )
        timings_ms["employee_predictions_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        items.sort(
            key=lambda item: (
                SoftwareMLService._risk_rank(item.target_column, item.predicted_band),
                item.confidence,
            ),
            reverse=True,
        )

        high_risk_count = sum(
            1 for item in items if SoftwareMLService._risk_bucket(target_column, item.predicted_band) == "high"
        )
        medium_risk_count = sum(
            1 for item in items if SoftwareMLService._risk_bucket(target_column, item.predicted_band) == "medium"
        )
        low_risk_count = sum(
            1 for item in items if SoftwareMLService._risk_bucket(target_column, item.predicted_band) == "low"
        )
        top_reasons = SoftwareMLService._top_driver_counts(items)
        team_summaries = SoftwareMLService._team_summaries(items)
        timings_ms["summaries_ms"] = round((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        team_analytics = SoftwareMLService._team_analytics(rows, artifact, target_column)
        timings_ms["team_analytics_ms"] = round((time.perf_counter() - stage_start) * 1000)

        from app.services.software_narrative_service import SoftwareNarrativeService

        stage_start = time.perf_counter()
        department_narrative = SoftwareNarrativeService.build_department_narrative(
            target_column=target_column,
            prediction_count=len(items),
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            top_reasons=top_reasons,
            team_summaries=team_summaries,
            allow_llm=use_llm_narrative and not llm_team,
        )
        team_narratives = SoftwareNarrativeService.build_team_narratives(
            target_column=target_column,
            team_summaries=team_summaries,
            allow_llm=use_llm_narrative,
            llm_team=llm_team,
        )
        timings_ms["narratives_ms"] = round((time.perf_counter() - stage_start) * 1000)
        timings_ms["total_ms"] = round((time.perf_counter() - start) * 1000)

        timing_payload = {
            "upload_id": upload_id,
            "target_column": target_column,
            "row_count": len(rows),
            "employee_group_count": len(grouped_rows),
            "prediction_count": len(items),
            "team_count": len(team_summaries),
            "use_llm_narrative": use_llm_narrative,
            "llm_team": llm_team,
            **timings_ms,
        }
        logger.info(
            "software_bulk_predict_timing %s",
            json.dumps(timing_payload, ensure_ascii=False, sort_keys=True),
            extra=timing_payload,
        )

        return SoftwareBulkPredictionResponse(
            department="software",
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
    def generate_department_dashboard(
        db: Session,
        *,
        current_user: User,
        upload_id: int | None = None,
        period: str = "week",
        target_column: str = "performance_band",
        use_llm: bool = False,
    ) -> SoftwareDepartmentDashboardResponse:
        if period not in {"week", "month", "quarter", "year"}:
            raise HTTPException(status_code=400, detail="period week, month, quarter veya year olmali.")

        department = SoftwareMLService._dashboard_department(db, current_user)
        employees = (
            db.query(Employee)
            .join(Employee.user)
            .filter(
                Employee.department_id == department.id,
                User.role == UserRole.employee,
            )
            .all()
        )
        teams = sorted({employee.team for employee in employees if employee.team})
        period_start = SoftwareMLService._dashboard_period_start(period)

        upload = SoftwareMLService._resolve_upload(db, upload_id) if upload_id else SoftwareMLService._latest_successful_upload(db)
        bulk = SoftwareMLService.predict_all_from_upload(
            db=db,
            upload_id=upload.id,
            target_column=target_column,
            use_llm_narrative=use_llm,
        )

        kpi_source = SoftwareMLService._dashboard_kpi_source(bulk)
        pulse_source = SoftwareMLService._dashboard_pulse_source(db, department.id, period_start)
        feedback_source = SoftwareMLService._dashboard_feedback_source(db, department.id, period_start)

        coverage = SoftwareMLService._dashboard_coverage(
            total_employees=len(employees),
            upload=upload,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
        )
        scores = SoftwareMLService._dashboard_scores(
            kpi_score=kpi_source["score"],
            pulse_score=pulse_source["score"],
            feedback_score=feedback_source["score"],
            kpi_risk=kpi_source["risk_score"],
            pulse_risk=pulse_source["risk_score"],
            feedback_risk=feedback_source["risk_score"],
            confidence_score=coverage.confidence_score,
            kpi_available=bool(kpi_source["employee_count"]),
            pulse_available=bool(pulse_source["employee_count"]),
            feedback_available=bool(feedback_source["employee_count"]),
        )
        insights = SoftwareMLService._dashboard_insights(
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            scores=scores,
            coverage=coverage,
            use_llm=use_llm,
        )
        team_breakdown = SoftwareMLService._dashboard_team_breakdown(
            employees=employees,
            teams=teams,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
        )
        actions = SoftwareMLService._dashboard_actions(insights, team_breakdown, scores)
        ai_summary = SoftwareMLService._dashboard_ai_summary(
            insights,
            actions,
            scores,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            coverage=coverage,
            use_llm=use_llm,
        )

        return SoftwareDepartmentDashboardResponse(
            status="success",
            department=DepartmentDashboardDepartmentResponse(
                id=department.id,
                name=department.name,
                member_count=len(employees),
                team_count=len(teams),
                teams=teams,
            ),
            period=period,
            generated_at=datetime.now(timezone.utc),
            upload_id=upload.id,
            coverage=coverage,
            scores=scores,
            sources={
                "kpiMl": DepartmentDashboardSourceResponse(
                    label="Performans Ciktilari (KPI/ML)",
                    score=kpi_source["score"],
                    status=SoftwareMLService._dashboard_status(kpi_source["score"]),
                    metrics=kpi_source["metrics"],
                    details=kpi_source["details"],
                ),
                "weeklyPulse": DepartmentDashboardSourceResponse(
                    label="Insan Sagligi Sinyalleri (Haftalik Nabiz)",
                    score=pulse_source["score"],
                    status=SoftwareMLService._dashboard_status(pulse_source["score"]),
                    metrics=pulse_source["metrics"],
                    details=pulse_source["details"],
                ),
                "feedback360": DepartmentDashboardSourceResponse(
                    label="Davranis ve Iliski Kalitesi (360 Feedback)",
                    score=feedback_source["score"],
                    status=SoftwareMLService._dashboard_status(feedback_source["score"]),
                    metrics=feedback_source["metrics"],
                    details=feedback_source["details"],
                ),
            },
            hybrid_insights=insights,
            team_breakdown=team_breakdown,
            actions=actions,
            ai_summary=ai_summary,
        )

    @staticmethod
    def _dashboard_department(db: Session, current_user: User) -> Department:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if current_user.role == UserRole.department_manager and current_employee and current_employee.department:
            return current_employee.department
        if current_user.role == UserRole.employee:
            raise HTTPException(status_code=403, detail="Departman dashboard'u manager veya admin erisimi gerektirir.")

        if current_employee and current_employee.department:
            return current_employee.department

        department = (
            db.query(Department)
            .filter(Department.name.ilike("%Yaz%"))
            .order_by(Department.id.asc())
            .first()
        )
        if not department:
            department = db.query(Department).order_by(Department.id.asc()).first()
        if not department:
            raise HTTPException(status_code=404, detail="Departman kaydi bulunamadi.")
        return department

    @staticmethod
    def _dashboard_period_start(period: str) -> date:
        today = datetime.now(timezone.utc).date()
        if period == "year":
            return today.replace(month=1, day=1)
        if period == "quarter":
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            return today.replace(month=quarter_month, day=1)
        if period == "month":
            return today.replace(day=1)
        return today - timedelta(days=7)

    @staticmethod
    def _dashboard_status(score: float) -> str:
        if score >= 85:
            return "success"
        if score >= 70:
            return "warning"
        return "danger"

    @staticmethod
    def _dashboard_avg(values: list[float | None]) -> float | None:
        numeric_values = [float(value) for value in values if value is not None]
        if not numeric_values:
            return None
        return round(sum(numeric_values) / len(numeric_values), 2)

    @staticmethod
    def _dashboard_clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return round(max(minimum, min(maximum, value)), 1)

    @staticmethod
    def _dashboard_scale_score(value: float | None) -> float | None:
        if value is None:
            return None
        value = float(value)
        if value <= 1.5:
            return SoftwareMLService._dashboard_clamp(value * 100)
        if value <= 5:
            return SoftwareMLService._dashboard_clamp(value * 20)
        return SoftwareMLService._dashboard_clamp(value)

    @staticmethod
    def _dashboard_risk_level_score(level: Any) -> float:
        raw = getattr(level, "value", level)
        return {"high": 85.0, "medium": 55.0, "low": 15.0}.get(str(raw or "").lower(), 35.0)

    @staticmethod
    def _dashboard_trend(values: list[float]) -> str:
        if len(values) < 2:
            return "stabil"
        delta = values[-1] - values[0]
        if delta > 3:
            return "yukselis"
        if delta < -3:
            return "dusus"
        return "stabil"

    @staticmethod
    def _dashboard_kpi_source(bulk: SoftwareBulkPredictionResponse) -> dict[str, Any]:
        total = max(bulk.prediction_count, 1)
        risk_score = SoftwareMLService._dashboard_clamp(
            ((bulk.high_risk_count * 100) + (bulk.medium_risk_count * 55) + (bulk.low_risk_count * 15)) / total
        )
        score = SoftwareMLService._dashboard_clamp(100 - risk_score)

        trend_values = [
            value
            for team in bulk.team_analytics
            for value in (team.get("trend_values") or [])
            if isinstance(value, (int, float))
        ]
        team_scores = {
            str(team.get("team")): {
                "score": SoftwareMLService._dashboard_clamp(100 - float(team.get("risk_score") or 0)),
                "risk": SoftwareMLService._dashboard_clamp(float(team.get("risk_score") or 0)),
                "trend": SoftwareMLService._dashboard_trend([float(v) for v in (team.get("trend_values") or []) if isinstance(v, (int, float))]),
            }
            for team in bulk.team_analytics
            if team.get("team")
        }

        return {
            "score": score,
            "risk_score": risk_score,
            "employee_count": bulk.prediction_count,
            "last_update": bulk.generated_at,
            "team_scores": team_scores,
            "metrics": {
                "averagePerformance": score,
                "targetAlignment": round((bulk.low_risk_count / total) * 100, 1),
                "trend": SoftwareMLService._dashboard_trend([float(value) for value in trend_values]),
                "mlRiskScore": risk_score,
                "highRiskCount": bulk.high_risk_count,
                "mediumRiskCount": bulk.medium_risk_count,
                "lowRiskCount": bulk.low_risk_count,
            },
            "details": {
                "predictionCount": bulk.prediction_count,
                "targetColumn": bulk.target_column,
                "teamAnalytics": bulk.team_analytics,
                "narrative": bulk.department_narrative,
            },
        }

    @staticmethod
    def _dashboard_pulse_source(db: Session, department_id: int, period_start: date) -> dict[str, Any]:
        rows = (
            db.query(SurveyResponse)
            .join(Employee)
            .filter(
                Employee.department_id == department_id,
                SurveyResponse.survey_type == "weekly_pulse",
                SurveyResponse.period_date >= period_start,
            )
            .all()
        )
        employee_ids = {row.employee_id for row in rows}
        motivation = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.score for row in rows]))
        mte = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.mte_score for row in rows]))
        ars = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.ars_score for row in rows]))
        score = motivation if motivation is not None else 0.0
        risk_score = ars if ars is not None else (100 - score if rows else 0.0)

        team_rows: dict[str, list[SurveyResponse]] = {}
        for row in rows:
            team = row.employee.team if row.employee else None
            if team:
                team_rows.setdefault(team, []).append(row)
        team_scores = {}
        for team, items in team_rows.items():
            team_score = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([item.score for item in items])) or 0.0
            team_ars = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([item.ars_score for item in items]))
            team_scores[team] = {
                "score": team_score,
                "risk": team_ars if team_ars is not None else 100 - team_score,
                "trend": "stabil",
            }

        return {
            "score": round(score, 1),
            "risk_score": round(risk_score, 1),
            "response_count": len(rows),
            "employee_count": len(employee_ids),
            "last_update": max((row.period_date for row in rows), default=None),
            "team_scores": team_scores,
            "metrics": {
                "motivationAverage": motivation,
                "motivationTrend": mte,
                "stressLevel": risk_score,
                "engagementScore": score,
                "attritionRisk": ars,
                "overallMood": SoftwareMLService._dashboard_status(score),
            },
            "details": {
                "dataAvailable": bool(rows),
                "responseCount": len(rows),
                "employeeCount": len(employee_ids),
            },
        }

    @staticmethod
    def _dashboard_feedback_source(db: Session, department_id: int, period_start: date) -> dict[str, Any]:
        rows = (
            db.query(FeedbackNLPAnalysis)
            .join(Employee, FeedbackNLPAnalysis.employee_id == Employee.id)
            .filter(
                Employee.department_id == department_id,
                FeedbackNLPAnalysis.department_id == department_id,
                FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
                FeedbackNLPAnalysis.created_at >= datetime.combine(period_start, datetime.min.time()),
            )
            .all()
        )
        employee_ids = {row.employee_id for row in rows}
        motivation = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.motivation_score for row in rows]))
        safety = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.psychological_safety_score for row in rows]))
        collaboration = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.collaboration_score for row in rows]))
        leadership = SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([row.leadership_support_score for row in rows]))
        score = SoftwareMLService._dashboard_avg([motivation, safety, collaboration, leadership])
        score = score if score is not None else 0.0
        risk_values = [
            SoftwareMLService._dashboard_risk_level_score(row.burnout_risk)
            for row in rows
            if row.burnout_risk is not None
        ] + [
            SoftwareMLService._dashboard_risk_level_score(row.flight_risk)
            for row in rows
            if row.flight_risk is not None
        ]
        risk_score = SoftwareMLService._dashboard_avg(risk_values)
        risk_score = risk_score if risk_score is not None else (100 - score if rows else 0.0)

        high_burnout = sum(1 for row in rows if row.burnout_risk == RiskLevel.high)
        high_flight = sum(1 for row in rows if row.flight_risk == RiskLevel.high)
        team_rows: dict[str, list[FeedbackNLPAnalysis]] = {}
        for row in rows:
            team = row.employee.team if row.employee else None
            if team:
                team_rows.setdefault(team, []).append(row)
        team_scores = {}
        for team, items in team_rows.items():
            team_score = SoftwareMLService._dashboard_avg([
                SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([item.motivation_score for item in items])),
                SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([item.psychological_safety_score for item in items])),
                SoftwareMLService._dashboard_scale_score(SoftwareMLService._dashboard_avg([item.collaboration_score for item in items])),
            ]) or 0.0
            team_scores[team] = {
                "score": team_score,
                "risk": 100 - team_score,
                "trend": "stabil",
            }

        return {
            "score": round(score, 1),
            "risk_score": round(risk_score, 1),
            "response_count": len(rows),
            "employee_count": len(employee_ids),
            "last_update": max((row.created_at for row in rows), default=None),
            "team_scores": team_scores,
            "metrics": {
                "motivationScore": motivation,
                "trustScore": safety,
                "collaborationScore": collaboration,
                "leadershipSupportScore": leadership,
                "burnoutRisk": round((high_burnout / max(len(rows), 1)) * 100, 1) if rows else None,
                "flightRisk": round((high_flight / max(len(rows), 1)) * 100, 1) if rows else None,
                "supportNeedFlag": bool(high_burnout or high_flight),
            },
            "details": {
                "dataAvailable": bool(rows),
                "responseCount": len(rows),
                "employeeCount": len(employee_ids),
                "highBurnoutCount": high_burnout,
                "highFlightRiskCount": high_flight,
            },
        }

    @staticmethod
    def _dashboard_coverage(
        *,
        total_employees: int,
        upload: DataUpload,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
    ) -> DepartmentDashboardCoverageResponse:
        denominator = max(total_employees, 1)
        kpi_pct = round((kpi_source["employee_count"] / denominator) * 100, 1)
        pulse_pct = round((pulse_source["employee_count"] / denominator) * 100, 1)
        feedback_pct = round((feedback_source["employee_count"] / denominator) * 100, 1)
        confidence = round((kpi_pct * 0.5) + (pulse_pct * 0.25) + (feedback_pct * 0.25), 1)
        return DepartmentDashboardCoverageResponse(
            kpi_employee_count=kpi_source["employee_count"],
            kpi_percentage=kpi_pct,
            pulse_response_count=pulse_source["response_count"],
            pulse_employee_count=pulse_source["employee_count"],
            pulse_percentage=pulse_pct,
            feedback_response_count=feedback_source["response_count"],
            feedback_employee_count=feedback_source["employee_count"],
            feedback_percentage=feedback_pct,
            confidence_score=confidence,
            last_kpi_update=upload.upload_date,
            last_pulse_update=pulse_source["last_update"],
            last_feedback_update=feedback_source["last_update"],
        )

    @staticmethod
    def _dashboard_scores(
        *,
        kpi_score: float,
        pulse_score: float,
        feedback_score: float,
        kpi_risk: float,
        pulse_risk: float,
        feedback_risk: float,
        confidence_score: float,
        kpi_available: bool,
        pulse_available: bool,
        feedback_available: bool,
    ) -> DepartmentDashboardScoresResponse:
        base_weights = {
            "kpiMl": 50.0 if kpi_available else 0.0,
            "weeklyPulse": 25.0 if pulse_available else 0.0,
            "feedback360": 25.0 if feedback_available else 0.0,
        }
        active_weight_total = sum(base_weights.values()) or 1.0
        normalized_weights = {
            key: round((value / active_weight_total) * 100, 1)
            for key, value in base_weights.items()
        }
        department_health = (
            (kpi_score * normalized_weights["kpiMl"])
            + (pulse_score * normalized_weights["weeklyPulse"])
            + (feedback_score * normalized_weights["feedback360"])
        ) / 100

        people_values = [
            value
            for value, available in [(pulse_score, pulse_available), (feedback_score, feedback_available)]
            if available
        ]
        people_health = sum(people_values) / len(people_values) if people_values else 0.0

        risk_values = [
            value
            for value, available in [(kpi_risk, kpi_available), (pulse_risk, pulse_available), (feedback_risk, feedback_available)]
            if available
        ]
        risk_score = sum(risk_values) / len(risk_values) if risk_values else 0.0
        return DepartmentDashboardScoresResponse(
            department_health=SoftwareMLService._dashboard_clamp(department_health),
            execution_score=SoftwareMLService._dashboard_clamp(kpi_score),
            people_health_score=SoftwareMLService._dashboard_clamp(people_health),
            risk_score=SoftwareMLService._dashboard_clamp(risk_score),
            confidence_score=SoftwareMLService._dashboard_clamp(confidence_score),
            weights=normalized_weights,
        )

    @staticmethod
    def _dashboard_insights(
        *,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        scores: DepartmentDashboardScoresResponse,
        coverage: DepartmentDashboardCoverageResponse,
        use_llm: bool = False,
    ) -> list[DepartmentDashboardInsightResponse]:
        insights: list[DepartmentDashboardInsightResponse] = []
        kpi = kpi_source["score"]
        pulse = pulse_source["score"]
        feedback = feedback_source["score"]
        feedback_available = bool(feedback_source.get("details", {}).get("dataAvailable"))
        common_evidence = SoftwareMLService._dashboard_common_evidence(
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            scores=scores,
            coverage=coverage,
        )

        if kpi >= 80 and pulse < 65:
            insights.append(DepartmentDashboardInsightResponse(
                type="performance_vs_health",
                severity="warning",
                title="Performans iyi, nabiz zayif",
                description=(
                    f"KPI/ML skoru {kpi:.0f}/100 ile iyi seviyede, ancak haftalik nabiz {pulse:.0f}/100. "
                    "Bu ayrisma ekip hedefleri tasirken motivasyon, stres veya baglilik tarafinda kirilganlik olabilecegini gosterir."
                ),
                recommendation="Kapasite, odak ve is yuku dengesi bu hafta takim liderleriyle gozden gecirilmeli.",
                action="this_week",
                evidence=common_evidence,
                manager_interpretation="Cikti iyi gorunse bile insan sinyali zayifladiginda surdurulebilirlik riski artar.",
                impact="Kisa vadede hedefler tutabilir; orta vadede burnout, kalite dususu veya teslim ritmi bozulmasi gorulebilir.",
                follow_up_metrics=["Nabiz motivasyon trendi", "Stres seviyesi", "KPI/ML performans skoru"],
            ))
        if feedback_available and feedback < 65 and kpi >= 70:
            insights.append(DepartmentDashboardInsightResponse(
                type="trust_vs_execution",
                severity="warning",
                title="Cikti var, iliski kalitesi zayif",
                description=(
                    f"360 skoru {feedback:.0f}/100 seviyesinde, KPI/ML skoru {kpi:.0f}/100. "
                    "Is akisi yuruyor fakat guven, is birligi veya destek sinyalleri ayni gucu gostermiyor."
                ),
                recommendation="Takim ici iletisim, code review ritmi ve destek ihtiyaci icin fasilite edilmis 1-on-1 planlanmali.",
                action="this_week",
                evidence=common_evidence,
                manager_interpretation="Performans tek basina saglikli ekip dinamiğini garanti etmiyor; iliski kalitesi ayrica takip edilmeli.",
                impact="Guven ve is birligi zayif kalirsa iyi KPI sonucu tekrar edilebilir olmaktan cikabilir.",
                follow_up_metrics=["360 psikolojik guven", "360 is birligi", "KPI/ML hedef uyumu"],
            ))
        if scores.risk_score >= 60:
            insights.append(DepartmentDashboardInsightResponse(
                type="risk_overlap",
                severity="critical",
                title="Birlesik risk yuksek: once KPI dususu, sonra insan sinyalleri dogrulanmali",
                description=(
                    f"Birlesik risk skoru {scores.risk_score:.0f}/100. KPI/ML performans {kpi:.0f}/100, "
                    f"insan sagligi {scores.people_health_score:.0f}/100 ve veri guveni {scores.confidence_score:.0f}/100. "
                    "Riskin ana kaynagi gercek kaynak kirilimlariyla birlikte okunmali."
                ),
                recommendation="48 saat icinde KPI dususunun takim/metrik kirilimi incelenmeli; nabiz ve 360 sinyalleriyle risk dogrulanmali.",
                action="urgent",
                evidence=common_evidence,
                manager_interpretation=(
                    "Bu tablo tek bir alarmdan cok, performans riski ile insan sinyallerinin birlikte ele alinmasi gereken "
                    "bir yonetim durumu oldugunu gosterir."
                ),
                impact="Erken aksiyon alinmazsa dusuk performans, ekip yorgunlugu ve veri eksiginden kaynaklanan karar belirsizligi ayni anda buyuyebilir.",
                follow_up_metrics=["KPI/ML performans skoru", "Nabiz stres seviyesi", "360 burnout sinyali", "Veri guveni"],
            ))
        if scores.confidence_score < 60:
            insights.append(DepartmentDashboardInsightResponse(
                type="coverage_gap",
                severity="info",
                title="Veri kapsama orani dusuk",
                description=(
                    f"Dashboard guven skoru {scores.confidence_score:.0f}/100. "
                    "Bazi kaynaklarda yeterli yanit olmadigi icin hibrit yorumun kanit seviyesi sinirli."
                ),
                recommendation="Nabiz ve 360 katilimi artirilarak hibrit skorun guvenilirligi yukseltilmeli.",
                action="monitoring",
                evidence=common_evidence,
                manager_interpretation="Skor hesaplanabilir, fakat eksik kaynaklar nedeniyle kararlar daha temkinli alinmali.",
                impact="Eksik kaynaklar tamamlanmadan riskin davranissal mi, operasyonel mi oldugu net ayrismayabilir.",
                follow_up_metrics=["Veri guveni", "Nabiz kapsama", "360 NLP kapsama"],
            ))
        if not feedback_available:
            insights.append(DepartmentDashboardInsightResponse(
                type="feedback_blind_spot",
                severity="warning" if scores.risk_score >= 50 else "info",
                title="360 NLP verisi eksik: davranissal risk kor noktasi var",
                description=(
                    "360 feedback NLP analizi olmadigi icin psikolojik guven, is birligi, destek ihtiyaci ve burnout "
                    "metin sinyalleri bu yorumda dogrulanamiyor."
                ),
                recommendation="Bu hafta 360 cevap kapsami artirilmali ve gelen metinler burnout/guven sinyalleri icin yeniden analiz edilmeli.",
                action="this_week" if scores.risk_score >= 50 else "monitoring",
                evidence=common_evidence,
                manager_interpretation="Insan sagligi yorumu su anda daha cok nabiz verisine dayaniyor; 360 eksigi davranissal kok nedeni belirsiz birakir.",
                impact="360 verisi gelmeden dusuk performansin iletisim, guven veya destek ihtiyaciyla iliskisi netlesmez.",
                follow_up_metrics=["360 cevap sayisi", "360 psikolojik guven", "360 burnout riski"],
            ))
        if not insights:
            insights.append(DepartmentDashboardInsightResponse(
                type="balanced_signal",
                severity="success",
                title="Kaynaklar dengeli gorunuyor",
                description="KPI/ML, haftalik nabiz ve 360 sinyalleri arasinda kritik bir cakisma gorunmuyor.",
                recommendation="Mevcut ritim korunup dusuk kapsama veya takim bazli sapmalar haftalik izlenmeli.",
                action="monitoring",
                evidence=common_evidence,
                manager_interpretation="Mevcut veri kaynaklari birbirini bozacak kuvvetli bir celiski uretmiyor.",
                impact="Bu durum izlemeyi birakmak anlamina gelmez; kapsama ve takim bazli sapmalar haftalik kontrol edilmeli.",
                follow_up_metrics=["Departman sagligi", "Birlesik risk", "Veri guveni"],
            ))
        if use_llm:
            return SoftwareMLService._dashboard_llm_insights(
                fallback=insights,
                kpi_source=kpi_source,
                pulse_source=pulse_source,
                feedback_source=feedback_source,
                scores=scores,
                coverage=coverage,
            )
        return insights

    @staticmethod
    def _dashboard_common_evidence(
        *,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        scores: DepartmentDashboardScoresResponse,
        coverage: DepartmentDashboardCoverageResponse,
    ) -> list[str]:
        feedback_available = bool(feedback_source.get("details", {}).get("dataAvailable"))
        feedback_text = (
            f"360: {feedback_source.get('score', 0):.0f}/100, {coverage.feedback_response_count} analiz"
            if feedback_available
            else "360: veri yok, davranissal/NLP sinyali skora katilamiyor"
        )
        return [
            f"KPI/ML: {kpi_source.get('score', 0):.0f}/100, {coverage.kpi_employee_count} calisan",
            f"Nabiz: {pulse_source.get('score', 0):.0f}/100, {coverage.pulse_response_count} cevap",
            feedback_text,
            f"Birlesik risk: {scores.risk_score:.0f}/100",
            f"Veri guveni: {scores.confidence_score:.0f}/100",
        ]

    @staticmethod
    def _dashboard_llm_insights(
        *,
        fallback: list[DepartmentDashboardInsightResponse],
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        scores: DepartmentDashboardScoresResponse,
        coverage: DepartmentDashboardCoverageResponse,
    ) -> list[DepartmentDashboardInsightResponse]:
        from app.services.software_narrative_service import SoftwareNarrativeService

        prompt = SoftwareMLService._dashboard_insight_prompt(
            fallback=fallback,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            scores=scores,
            coverage=coverage,
        )
        raw_output, provider, model_name, errors = SoftwareNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=24,
        )
        sanitized = SoftwareMLService._sanitize_dashboard_llm_insights(
            raw_output=raw_output,
            provider=provider,
            model_name=model_name,
        )
        if sanitized:
            return sanitized

        reason = (
            f"LLM yaniti alinamadi veya beklenen JSON formatinda degildi ({'; '.join(errors)})."
            if provider
            else "LLM provider ayarli degil."
        )
        enriched: list[DepartmentDashboardInsightResponse] = []
        for item in fallback:
            item.source = "deterministic_llm_fallback"
            item.fallback_used = True
            item.impact = item.impact or reason
            enriched.append(item)
        return enriched

    @staticmethod
    def _dashboard_insight_prompt(
        *,
        fallback: list[DepartmentDashboardInsightResponse],
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        scores: DepartmentDashboardScoresResponse,
        coverage: DepartmentDashboardCoverageResponse,
    ) -> str:
        payload = {
            "scores": {
                "departmentHealth": scores.department_health,
                "kpiMlPerformance": scores.execution_score,
                "peopleHealth": scores.people_health_score,
                "risk": scores.risk_score,
                "confidence": scores.confidence_score,
                "weights": scores.weights,
            },
            "coverage": {
                "kpiEmployeeCount": coverage.kpi_employee_count,
                "kpiPercentage": coverage.kpi_percentage,
                "pulseResponseCount": coverage.pulse_response_count,
                "pulseEmployeeCount": coverage.pulse_employee_count,
                "pulsePercentage": coverage.pulse_percentage,
                "feedbackResponseCount": coverage.feedback_response_count,
                "feedbackEmployeeCount": coverage.feedback_employee_count,
                "feedbackPercentage": coverage.feedback_percentage,
            },
            "sources": {
                "kpiMl": {
                    "score": kpi_source.get("score"),
                    "risk": kpi_source.get("risk_score"),
                    "metrics": kpi_source.get("metrics"),
                    "details": kpi_source.get("details"),
                },
                "weeklyPulse": {
                    "score": pulse_source.get("score"),
                    "risk": pulse_source.get("risk_score"),
                    "metrics": pulse_source.get("metrics"),
                    "details": pulse_source.get("details"),
                },
                "feedback360": {
                    "score": feedback_source.get("score"),
                    "risk": feedback_source.get("risk_score"),
                    "metrics": feedback_source.get("metrics"),
                    "details": feedback_source.get("details"),
                },
            },
            "ruleBasedSignals": [
                {
                    "type": item.type,
                    "severity": item.severity,
                    "title": item.title,
                    "description": item.description,
                    "evidence": item.evidence,
                    "recommendation": item.recommendation,
                }
                for item in fallback
            ],
        }
        return (
            "Sen kidemli bir yazilim departmani yoneticisi, people analytics danismani ve organizasyon psikologusun.\n"
            "Gorevin: KPI/ML, haftalik nabiz ve 360 feedback kaynaklarini birlikte yorumlayarak yonetici icin detayli hibrit icgoruler uretmek.\n"
            "Kurallar:\n"
            "- Sadece verilen PAYLOAD verisini kullan; yeni sayi, yeni metrik, yeni olay uydurma.\n"
            "- Sayilari yuvarlama disinda degistirme.\n"
            "- 360 verisi yoksa bunu acikca 'dogrulanamiyor' diye belirt; 360 sonucu varmis gibi yorumlama.\n"
            "- Riskleri kisi suclayan dille degil, kapasite/surec/motivasyon/guven baglaminda yorumla.\n"
            "- Her icgoru yoneticinin neden ilgilenmesi gerektigini ve hangi veriyle dogrulayacagini aciklasin.\n"
            "- Aksiyonlar uygulanabilir olsun: kim, neye bakacak, hangi kaynakla dogrulayacak, ne zaman.\n"
            "- Sadece gecerli JSON dondur.\n"
            "JSON semasi: {"
            '"insights": ['
            '{"type": "string", "severity": "critical|warning|info|success", "title": "string", '
            '"description": "string", "evidence": ["string"], "manager_interpretation": "string", '
            '"impact": "string", "recommendation": "string", "action": "urgent|this_week|monitoring", '
            '"follow_up_metrics": ["string"], "team": null}'
            "]}\n"
            "Icerik beklentisi:\n"
            "- 1 ile 4 arasi icgoru uret.\n"
            "- description: Ana durum ve nedeni, 2-3 cumle.\n"
            "- evidence: Verilen sayilardan 3-5 madde.\n"
            "- manager_interpretation: Yonetici bu sinyali nasil okumali, 1-2 cumle.\n"
            "- impact: Aksiyon alinmazsa veya veri tamamlanmazsa etkisi ne olur, 1-2 cumle.\n"
            "- recommendation: Somut ve zamanli aksiyon, 1 cumle.\n"
            f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
        )

    @staticmethod
    def _sanitize_dashboard_llm_insights(
        *,
        raw_output: str | None,
        provider: str | None,
        model_name: str | None,
    ) -> list[DepartmentDashboardInsightResponse] | None:
        from app.services.software_narrative_service import SoftwareNarrativeService

        if not raw_output:
            return None
        text = raw_output.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        raw_insights = payload.get("insights")
        if not isinstance(raw_insights, list):
            return None

        rows: list[DepartmentDashboardInsightResponse] = []
        for raw_item in raw_insights[:4]:
            if not isinstance(raw_item, dict):
                continue
            title = SoftwareNarrativeService._clean_text(raw_item.get("title"), 180)
            description = SoftwareNarrativeService._clean_text(raw_item.get("description"), 900)
            recommendation = SoftwareNarrativeService._clean_text(raw_item.get("recommendation"), 320)
            if not title or not description or not recommendation:
                continue
            severity = str(raw_item.get("severity") or "info").lower()
            if severity not in {"critical", "warning", "info", "success"}:
                severity = "info"
            action = str(raw_item.get("action") or "monitoring").lower()
            if action not in {"urgent", "this_week", "monitoring"}:
                action = "urgent" if severity == "critical" else "this_week" if severity == "warning" else "monitoring"
            rows.append(DepartmentDashboardInsightResponse(
                type=SoftwareNarrativeService._clean_text(raw_item.get("type"), 80) or "llm_hybrid_insight",
                severity=severity,
                title=title,
                description=description,
                recommendation=recommendation,
                action=action,
                team=SoftwareNarrativeService._clean_text(raw_item.get("team"), 80) or None,
                evidence=SoftwareNarrativeService._sanitize_text_list(raw_item.get("evidence"), 5, 220),
                manager_interpretation=SoftwareNarrativeService._clean_text(raw_item.get("manager_interpretation"), 520),
                impact=SoftwareNarrativeService._clean_text(raw_item.get("impact"), 520),
                follow_up_metrics=SoftwareNarrativeService._sanitize_text_list(raw_item.get("follow_up_metrics"), 5, 100),
                source=provider or "llm",
                model=model_name,
                fallback_used=False,
            ))
        return rows or None

    @staticmethod
    def _dashboard_team_breakdown(
        *,
        employees: list[Employee],
        teams: list[str],
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
    ) -> list[DepartmentDashboardTeamResponse]:
        counts = {team: sum(1 for employee in employees if employee.team == team) for team in teams}
        rows: list[DepartmentDashboardTeamResponse] = []
        for team in teams:
            kpi = (kpi_source["team_scores"].get(team) or {}).get("score", kpi_source["score"])
            pulse = (pulse_source["team_scores"].get(team) or {}).get("score", pulse_source["score"])
            feedback = (feedback_source["team_scores"].get(team) or {}).get("score", feedback_source["score"])
            health = (kpi * 0.5) + (pulse * 0.25) + (feedback * 0.25)
            risk = (
                (kpi_source["team_scores"].get(team) or {}).get("risk", kpi_source["risk_score"])
                + (pulse_source["team_scores"].get(team) or {}).get("risk", pulse_source["risk_score"])
                + (feedback_source["team_scores"].get(team) or {}).get("risk", feedback_source["risk_score"])
            ) / 3
            rows.append(DepartmentDashboardTeamResponse(
                team=team,
                member_count=counts.get(team, 0),
                scores={
                    "health": SoftwareMLService._dashboard_clamp(health),
                    "kpi": SoftwareMLService._dashboard_clamp(kpi),
                    "pulse": SoftwareMLService._dashboard_clamp(pulse),
                    "feedback": SoftwareMLService._dashboard_clamp(feedback),
                    "risk": SoftwareMLService._dashboard_clamp(risk),
                },
                metrics={
                    "performance": kpi,
                    "motivation": pulse,
                    "trustScore": feedback,
                },
                status=SoftwareMLService._dashboard_status(health),
                trend=(kpi_source["team_scores"].get(team) or {}).get("trend", "stabil"),
            ))
        return sorted(rows, key=lambda item: item.scores.get("health", 0))

    @staticmethod
    def _dashboard_actions(
        insights: list[DepartmentDashboardInsightResponse],
        team_breakdown: list[DepartmentDashboardTeamResponse],
        scores: DepartmentDashboardScoresResponse,
    ) -> DepartmentDashboardActionsResponse:
        urgent: list[DepartmentDashboardActionResponse] = []
        this_week: list[DepartmentDashboardActionResponse] = []
        monitoring: list[DepartmentDashboardActionResponse] = []

        for insight in insights:
            evidence_text = "; ".join(insight.evidence[:3]) if insight.evidence else insight.description
            action = DepartmentDashboardActionResponse(
                title=insight.recommendation,
                description=(
                    f"Dayanak: {evidence_text}. "
                    f"Yonetici yorumu: {insight.manager_interpretation or insight.description}"
                ),
                priority="P0" if insight.severity == "critical" else ("P1" if insight.severity == "warning" else "P2"),
                due_date="48 saat" if insight.severity == "critical" else ("Bu hafta" if insight.severity == "warning" else "Haftalik"),
                owner="Manager + HR" if insight.severity == "critical" else "Manager",
                source=insight.type,
            )
            if insight.severity == "critical":
                urgent.append(action)
            elif insight.severity == "warning":
                this_week.append(action)
            else:
                monitoring.append(action)

        for team in team_breakdown[:3]:
            health = float(team.scores.get("health", 100))
            if health < 70:
                kpi = float(team.scores.get("kpi", 0))
                pulse = float(team.scores.get("pulse", 0))
                feedback = float(team.scores.get("feedback", 0))
                risk = float(team.scores.get("risk", 0))
                weakest = min(
                    [
                        ("KPI/ML", kpi),
                        ("Nabiz", pulse),
                        ("360", feedback),
                    ],
                    key=lambda item: item[1],
                )
                monitoring.append(DepartmentDashboardActionResponse(
                    title=f"{team.team} icin {weakest[0]} kaynakli saglik dususunu incele",
                    description=(
                        f"Dayanak: hibrit saglik {health:.1f}/100, KPI/ML {kpi:.1f}/100, "
                        f"nabiz {pulse:.1f}/100, 360 {feedback:.1f}/100, risk {risk:.1f}/100. "
                        f"En zayif kaynak {weakest[0]} oldugu icin takim lideriyle bu kirilim dogrulanmali."
                    ),
                    priority="P2",
                    due_date="Haftalik",
                    owner="Team Lead",
                    source="team_breakdown",
                ))

        if scores.confidence_score < 60:
            monitoring.append(DepartmentDashboardActionResponse(
                title="Veri kapsamasini artir",
                description=(
                    f"Dayanak: veri guveni {scores.confidence_score:.1f}/100. "
                    "Nabiz ve 360 katilimi dusuk oldugunda hibrit yorumlarin guveni azalir."
                ),
                priority="P2",
                due_date="Bu hafta",
                owner="Manager",
                source="coverage",
            ))

        return DepartmentDashboardActionsResponse(
            urgent=urgent,
            this_week=this_week,
            monitoring=monitoring,
        )

    @staticmethod
    def _dashboard_ai_summary(
        insights: list[DepartmentDashboardInsightResponse],
        actions: DepartmentDashboardActionsResponse,
        scores: DepartmentDashboardScoresResponse,
        *,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        coverage: DepartmentDashboardCoverageResponse,
        use_llm: bool = False,
    ) -> DepartmentDashboardAISummaryResponse:
        fallback = SoftwareMLService._dashboard_ai_summary_fallback(insights, actions, scores)
        if not use_llm:
            return fallback

        llm_summary = SoftwareMLService._dashboard_llm_ai_summary(
            fallback=fallback,
            insights=insights,
            actions=actions,
            scores=scores,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            coverage=coverage,
        )
        return llm_summary or fallback

    @staticmethod
    def _dashboard_ai_summary_fallback(
        insights: list[DepartmentDashboardInsightResponse],
        actions: DepartmentDashboardActionsResponse,
        scores: DepartmentDashboardScoresResponse,
    ) -> DepartmentDashboardAISummaryResponse:
        risk_titles = [item.title for item in insights if item.severity in {"critical", "warning"}]
        recommendations = [item.title for item in actions.urgent + actions.this_week][:5]
        strengths = []
        if scores.execution_score >= 80:
            strengths.append("KPI/ML performans sinyali guclu.")
        if scores.people_health_score >= 75:
            strengths.append("Insan sagligi kaynaklari dengeli gorunuyor.")
        if not strengths:
            strengths.append("KPI/ML, nabiz ve 360 verileri birlikte okunabilir bir karar resmi sunuyor.")
        summary = (
            f"Departman saglik skoru {scores.department_health}/100. "
            f"Performans {scores.execution_score}/100, insan sagligi {scores.people_health_score}/100, "
            f"birlesik risk {scores.risk_score}/100 ve veri guveni {scores.confidence_score}/100. "
            "Bu ozet backend kural bazli analiz katmani tarafindan, mevcut KPI/ML, nabiz ve 360 sinyallerine gore uretilmistir."
        )
        return DepartmentDashboardAISummaryResponse(
            summary=summary,
            strengths=strengths,
            risks=risk_titles,
            recommendations=recommendations,
            source="deterministic",
            fallback_used=True,
        )

    @staticmethod
    def _dashboard_llm_ai_summary(
        *,
        fallback: DepartmentDashboardAISummaryResponse,
        insights: list[DepartmentDashboardInsightResponse],
        actions: DepartmentDashboardActionsResponse,
        scores: DepartmentDashboardScoresResponse,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        coverage: DepartmentDashboardCoverageResponse,
    ) -> DepartmentDashboardAISummaryResponse | None:
        from app.services.software_narrative_service import SoftwareNarrativeService

        prompt = SoftwareMLService._dashboard_ai_summary_prompt(
            insights=insights,
            actions=actions,
            scores=scores,
            kpi_source=kpi_source,
            pulse_source=pulse_source,
            feedback_source=feedback_source,
            coverage=coverage,
        )
        raw_output, provider, model_name, errors = SoftwareNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=24,
        )
        summary = SoftwareMLService._sanitize_dashboard_ai_summary(
            raw_output=raw_output,
            provider=provider,
            model_name=model_name,
        )
        if summary:
            return summary

        enriched = fallback.model_copy()
        enriched.source = "deterministic_llm_fallback"
        enriched.model = model_name
        enriched.fallback_used = True
        reason = (
            f"LLM ozeti alinamadi veya beklenen JSON formatinda degildi ({'; '.join(errors)})."
            if provider
            else "LLM provider ayarli degil."
        )
        enriched.recommendations = [*enriched.recommendations[:4], reason][:5]
        return enriched

    @staticmethod
    def _dashboard_ai_summary_prompt(
        *,
        insights: list[DepartmentDashboardInsightResponse],
        actions: DepartmentDashboardActionsResponse,
        scores: DepartmentDashboardScoresResponse,
        kpi_source: dict[str, Any],
        pulse_source: dict[str, Any],
        feedback_source: dict[str, Any],
        coverage: DepartmentDashboardCoverageResponse,
    ) -> str:
        payload = {
            "scores": {
                "departmentHealth": scores.department_health,
                "kpiMlPerformance": scores.execution_score,
                "peopleHealth": scores.people_health_score,
                "risk": scores.risk_score,
                "confidence": scores.confidence_score,
                "weights": scores.weights,
            },
            "coverage": {
                "kpiEmployeeCount": coverage.kpi_employee_count,
                "kpiPercentage": coverage.kpi_percentage,
                "pulseResponseCount": coverage.pulse_response_count,
                "pulseEmployeeCount": coverage.pulse_employee_count,
                "pulsePercentage": coverage.pulse_percentage,
                "feedbackResponseCount": coverage.feedback_response_count,
                "feedbackEmployeeCount": coverage.feedback_employee_count,
                "feedbackPercentage": coverage.feedback_percentage,
            },
            "sources": {
                "kpiMl": {
                    "score": kpi_source.get("score"),
                    "risk": kpi_source.get("risk_score"),
                    "metrics": kpi_source.get("metrics"),
                    "details": kpi_source.get("details"),
                },
                "weeklyPulse": {
                    "score": pulse_source.get("score"),
                    "risk": pulse_source.get("risk_score"),
                    "metrics": pulse_source.get("metrics"),
                    "details": pulse_source.get("details"),
                },
                "feedback360": {
                    "score": feedback_source.get("score"),
                    "risk": feedback_source.get("risk_score"),
                    "metrics": feedback_source.get("metrics"),
                    "details": feedback_source.get("details"),
                },
            },
            "hybridInsights": [
                {
                    "type": item.type,
                    "severity": item.severity,
                    "title": item.title,
                    "description": item.description,
                    "evidence": item.evidence,
                    "managerInterpretation": item.manager_interpretation,
                    "impact": item.impact,
                    "recommendation": item.recommendation,
                    "followUpMetrics": item.follow_up_metrics,
                }
                for item in insights[:4]
            ],
            "actions": {
                "urgent": [item.model_dump() for item in actions.urgent[:3]],
                "thisWeek": [item.model_dump() for item in actions.this_week[:3]],
                "monitoring": [item.model_dump() for item in actions.monitoring[:3]],
            },
        }
        return (
            "Sen kidemli bir yazilim departmani direktoru, people analytics uzmani ve organizasyon psikologusun.\n"
            "Gorevin: Hibrit dashboard verilerini yoneticiye okunabilir tek bir AI ozet raporu olarak yorumlamak.\n"
            "Kurallar:\n"
            "- Sadece PAYLOAD icindeki gercek sayilari ve sinyalleri kullan; yeni sayi, yeni metrik, yeni olay uydurma.\n"
            "- 360 verisi yoksa psikolojik guven/is birligi/burnout tarafinin dogrulanamadigini acikca soyle.\n"
            "- Summary 4-6 cumle olsun: once genel durum, sonra ana risk kaynagi, sonra insan/kultur sinyali, sonra veri guveni ve karar odaği.\n"
            "- Strengths bolumu 'olumlu' diye zorlama yapmasin; veri guveni, takip edilebilirlik veya eldeki kanit gucu gibi gercek guclu noktalar olabilir.\n"
            "- Risks bolumu sadece baslik listesi degil, 1-2 cumlelik risk aciklamalari olsun.\n"
            "- Recommendations bolumu somut, sirali ve yonetici aksiyonuna uygun olsun.\n"
            "- Kisileri suclayan dil kullanma; kapasite, surec, motivasyon, guven ve destek baglaminda yaz.\n"
            "- Sadece gecerli JSON dondur.\n"
            "JSON semasi: {"
            '"summary": "string", '
            '"strengths": ["string"], '
            '"risks": ["string"], '
            '"recommendations": ["string"]'
            "}\n"
            f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
        )

    @staticmethod
    def _sanitize_dashboard_ai_summary(
        *,
        raw_output: str | None,
        provider: str | None,
        model_name: str | None,
    ) -> DepartmentDashboardAISummaryResponse | None:
        from app.services.software_narrative_service import SoftwareNarrativeService

        if not raw_output:
            return None
        text = raw_output.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None

        summary = SoftwareNarrativeService._clean_text(payload.get("summary"), 1400)
        if not summary:
            return None
        return DepartmentDashboardAISummaryResponse(
            summary=summary,
            strengths=SoftwareNarrativeService._sanitize_text_list(payload.get("strengths"), 4, 360),
            risks=SoftwareNarrativeService._sanitize_text_list(payload.get("risks"), 4, 420),
            recommendations=SoftwareNarrativeService._sanitize_text_list(payload.get("recommendations"), 5, 420),
            source=provider or "llm",
            model=model_name,
            fallback_used=False,
        )

    @staticmethod
    def generate_department_insights(
        db: Session,
        *,
        upload_id: int | None = None,
        period: str = "week",
        target_column: str = "performance_band",
        use_llm: bool = True,
    ) -> SoftwareDepartmentInsightsResponse:
        upload = SoftwareMLService._resolve_upload(db, upload_id) if upload_id else SoftwareMLService._latest_successful_upload(db)
        bulk = SoftwareMLService.predict_all_from_upload(
            db=db,
            upload_id=upload.id,
            target_column=target_column,
            use_llm_narrative=use_llm,
        )
        narrative = bulk.department_narrative or {}
        manager_summary = narrative.get("manager_summary") or "Departman icin AI ozeti henuz olusmadi."
        risk_interpretation = narrative.get("risk_interpretation") or ""
        action_plan = narrative.get("action_plan") or []
        talking_points = narrative.get("leadership_talking_points") or []
        confidence_note = narrative.get("confidence_note") or ""
        health_score = SoftwareMLService._department_health_score(bulk)

        team_notes = []
        for team in (bulk.team_analytics or [])[:4]:
            team_name = team.get("team") or "Takim"
            latest_score = team.get("latest_score")
            trend_delta = team.get("trend_delta")
            team_notes.append(f"{team_name}: son skor {latest_score if latest_score is not None else '-'}, trend {trend_delta if trend_delta is not None else '-'}.")

        action_lines = [
            f"- {item.get('title') or item.get('reason')}"
            for item in action_plan
            if item.get("title") or item.get("reason")
        ]
        talking_lines = [f"- {item}" for item in talking_points]
        team_lines = [f"- {item}" for item in team_notes]

        insights = "\n".join(
            part for part in [
                "1. OZET",
                manager_summary,
                "",
                "2. GUCLU YONLER",
                "\n".join(team_lines) if team_lines else "Takim bazli olumlu sinyaller backend verisi geldikce netlesecek.",
                "",
                "3. GELISTIRME ALANLARI",
                risk_interpretation or "Risk alanlari model tahminleri ve KPI driver tekrarlarina gore izleniyor.",
                "",
                "4. DEPARTMAN SAGLIGI",
                f"Genel saglik puani: {health_score}/100. Yuksek risk: {bulk.high_risk_count}, orta risk: {bulk.medium_risk_count}, dusuk risk: {bulk.low_risk_count}.",
                "",
                "5. ONERILER",
                "\n".join(action_lines) if action_lines else "Bu hafta icin otomatik aksiyon onerisi olusmadi.",
                "",
                "6. SONRAKI HAFTA BEKLENTISI",
                "\n".join(talking_lines) if talking_lines else "Takim liderleriyle kapasite, odak ve risk sinyalleri haftalik olarak takip edilmeli.",
                "",
                confidence_note,
            ] if part is not None
        )

        return SoftwareDepartmentInsightsResponse(
            status="success",
            department="software",
            upload_id=upload.id,
            period=period,
            insights=insights,
            generated_at=datetime.now(timezone.utc),
            source=str(narrative.get("source") or "deterministic"),
            model=narrative.get("model"),
            fallback_used=bool(narrative.get("fallback_used", False)),
            health_score=health_score,
            sections={
                "summary": manager_summary,
                "strengths": team_notes,
                "improvement_areas": [risk_interpretation] if risk_interpretation else [],
                "next_week": talking_points,
            },
            actions=action_plan,
        )

    @staticmethod
    def _department_health_score(bulk: SoftwareBulkPredictionResponse) -> float:
        total = max(bulk.prediction_count, 1)
        penalty = (bulk.high_risk_count * 18) + (bulk.medium_risk_count * 8)
        score = 100 - (penalty / total)
        return round(max(0, min(100, score)), 1)

    @staticmethod
    def _top_driver_counts(items: list[SoftwarePredictionResponse], limit: int = 5) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for item in items:
            driver_name = "KPI sinyali"
            if item.top_drivers:
                driver_name = str(item.top_drivers[0].get("metric_name") or driver_name)
            counts[driver_name] = counts.get(driver_name, 0) + 1
        return sorted(counts.items(), key=lambda entry: entry[1], reverse=True)[:limit]

    @staticmethod
    def _team_summaries(items: list[SoftwarePredictionResponse]) -> list[dict[str, Any]]:
        grouped: dict[str, list[SoftwarePredictionResponse]] = {}
        for item in items:
            team = str(item.summary_payload.get("team") or "Takim bilgisi yok")
            grouped.setdefault(team, []).append(item)

        summaries: list[dict[str, Any]] = []
        for team, team_items in grouped.items():
            high = sum(1 for item in team_items if SoftwareMLService._risk_bucket(item.target_column, item.predicted_band) == "high")
            medium = sum(1 for item in team_items if SoftwareMLService._risk_bucket(item.target_column, item.predicted_band) == "medium")
            low = sum(1 for item in team_items if SoftwareMLService._risk_bucket(item.target_column, item.predicted_band) == "low")
            top_reason = SoftwareMLService._top_driver_counts(team_items, limit=1)[0][0]
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
    def _probability_risk_score(target_column: str, probabilities: dict[str, float], predicted_band: str | None = None) -> int:
        if target_column == "attrition_risk_band":
            score = (
                probabilities.get("Yuksek", 0.0) * 100
                + probabilities.get("Orta", 0.0) * 55
                + probabilities.get("Dusuk", 0.0) * 15
            )
            if not probabilities and predicted_band:
                score = {"Yuksek": 85, "Orta": 55, "Dusuk": 20}.get(predicted_band, 50)
            return int(round(score))

        score = (
            probabilities.get("Riskli", 0.0) * 100
            + probabilities.get("Stabil", 0.0) * 55
            + probabilities.get("Yuksek", 0.0) * 20
            + probabilities.get("Guclu", 0.0) * 10
        )
        if not probabilities and predicted_band:
            score = {"Riskli": 85, "Stabil": 55, "Yuksek": 20, "Guclu": 10}.get(predicted_band, 50)
        return int(round(score))

    @staticmethod
    def _team_analytics(rows: list[dict[str, Any]], artifact: Any, target_column: str) -> list[dict[str, Any]]:
        dataset = SoftwareFeatureBuilder.build_from_rows(rows)
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
            score = SoftwareMLService._probability_risk_score(target_column, probabilities, predicted_band)
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

    @staticmethod
    def predict_all_targets(
        db: Session,
        upload_id: int,
        use_llm_narrative: bool = False,
    ):
        """4 binary hedef için toplu tahmin — satış servisindeki ile aynı yapı."""
        from app.schemas.analytics import (
            SalesAllTargetsBulkResponse,
            SalesEmployeeAllTargets,
            SalesTargetResult,
        )

        TARGET_MAP = {
            "Performance_Drop_Target": "perf_drop",
            "Burnout_Target":          "burnout",
            "Resignation_Target":      "resignation",
            "High_Risk_Target":        "high_risk",
        }

        # Her hedef için bulk tahmin çalıştır
        target_items: dict[str, list] = {}
        base_bulk = None
        for target_col, field_name in TARGET_MAP.items():
            try:
                bulk = SoftwareMLService.predict_all_from_upload(
                    db=db,
                    upload_id=upload_id,
                    target_column=target_col,
                    use_llm_narrative=(use_llm_narrative and target_col == "Performance_Drop_Target"),
                )
                target_items[target_col] = bulk.items
                if target_col == "Performance_Drop_Target":
                    base_bulk = bulk
            except Exception:
                target_items[target_col] = []

        # Çalışan bazında birleştir
        emp_map: dict[int, dict] = {}
        for target_col, items in target_items.items():
            field_name = TARGET_MAP[target_col]
            for item in items:
                eid = item.employee_id
                if eid not in emp_map:
                    sp = item.summary_payload
                    emp_map[eid] = {
                        "employee_id":            eid,
                        "employee_name":          sp.get("employee_name"),
                        "team":                   sp.get("team"),
                        "role":                   sp.get("role"),
                        "external_employee_code": sp.get("external_employee_code"),
                        "top_drivers":            item.top_drivers or [],
                        "recommended_actions":    item.recommended_actions or [],
                        "perf_drop":   None,
                        "burnout":     None,
                        "resignation": None,
                        "high_risk":   None,
                    }
                emp_map[eid][field_name] = SalesTargetResult(
                    predicted_band=str(item.predicted_band),
                    confidence=round(item.confidence, 4),
                )

        def _risk_score(e: dict) -> float:
            score = 0.0
            weights = {"perf_drop": 0.35, "burnout": 0.20, "resignation": 0.25, "high_risk": 0.20}
            for field, w in weights.items():
                r = e.get(field)
                if r is None:
                    continue
                band = r.predicted_band if hasattr(r, "predicted_band") else r.get("predicted_band")
                conf = r.confidence if hasattr(r, "confidence") else r.get("confidence", 0)
                if str(band) == "1":
                    score += conf * w
            return score

        emp_list = list(emp_map.values())
        emp_list.sort(key=_risk_score, reverse=True)
        employees = [SalesEmployeeAllTargets(**e) for e in emp_list]

        from datetime import datetime, timezone
        return SalesAllTargetsBulkResponse(
            upload_id=upload_id,
            employee_count=len(employees),
            employees=employees,
            department_narrative=base_bulk.department_narrative if base_bulk else None,
            team_analytics=base_bulk.team_analytics if base_bulk else [],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
