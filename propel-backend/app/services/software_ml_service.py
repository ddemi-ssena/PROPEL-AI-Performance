from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.artifacts.software import SoftwareArtifactStore
from app.analytics.prediction.software import SoftwarePredictionService
from app.analytics.training.software import SoftwareBaselineTrainer
from app.db.models.data_upload import DataUpload
from app.db.models.employee import Employee
from app.schemas.analytics import (
    SoftwareBulkPredictionResponse,
    SoftwareDatasetEmployeeResponse,
    SoftwareDatasetResponse,
    SoftwareModelStateResponse,
    SoftwareModelTrainResponse,
    SoftwarePredictionResponse,
)


UPLOAD_DIR = Path("uploads")
SUPPORTED_TARGETS = {"performance_band", "attrition_risk_band"}
SUPPORTED_MODELS = {"logistic_regression", "random_forest", "hist_gradient_boosting"}
TARGET_LABELS = {
    "performance_band": "Performans",
    "attrition_risk_band": "Ayrilma Riski",
}


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
            if (upload.raw_info or {}).get("department_key") == "software"
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

        employees: dict[int, dict[str, Any]] = {}
        for row in rows:
            raw_employee_id = row.get("employee_id")
            if raw_employee_id in (None, ""):
                continue
            try:
                employee_id = int(float(raw_employee_id))
            except (TypeError, ValueError):
                continue

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
            metadata_path = artifact_dir / "metadata.json"
            metadata: dict[str, Any] = {}
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
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
    def _resolve_upload(db: Session, upload_id: int) -> DataUpload:
        upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Yukleme kaydi bulunamadi.")
        if upload.status != "Success":
            raise HTTPException(status_code=400, detail="Sadece basarili yuklemeler ML egitiminde kullanilabilir.")

        department_key = (upload.raw_info or {}).get("department_key")
        if department_key and department_key != "software":
            raise HTTPException(status_code=400, detail="Bu endpoint yalnizca software upload'lari icindir.")

        return upload

    @staticmethod
    def _upload_path(upload: DataUpload) -> Path:
        path = UPLOAD_DIR / f"{upload.id}_{upload.file_name}"
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Yuklenen dosya bulunamadi: {path}")
        return path

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

        raise HTTPException(
            status_code=400,
            detail="ML egitimi icin su anda CSV veya JSON upload destekleniyor.",
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
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))

        try:
            result = SoftwareBaselineTrainer.train(
                rows,
                target_column=target_column,
                model_name=model_name,  # type: ignore[arg-type]
                test_period_count=test_period_count,
            )
            artifact = SoftwareArtifactStore().save_training_result(result, upload_id=upload_id)
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
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))
        grouped_rows: dict[int, list[dict[str, Any]]] = {}

        for row in rows:
            raw_employee_id = row.get("employee_id")
            if raw_employee_id in (None, ""):
                continue
            try:
                employee_id = int(float(raw_employee_id))
            except (TypeError, ValueError):
                continue
            grouped_rows.setdefault(employee_id, []).append(row)

        if not grouped_rows:
            raise HTTPException(status_code=404, detail="Upload icinde tahmin icin employee_id bulunamadi.")

        try:
            artifact = SoftwareArtifactStore().load(target_column)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"{target_column} icin egitilmis software model artifact'i bulunamadi.",
            ) from exc

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
        from app.services.software_narrative_service import SoftwareNarrativeService

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

        return SoftwareBulkPredictionResponse(
            department="software",
            upload_id=upload_id,
            target_column=target_column,
            prediction_count=len(items),
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            department_narrative=department_narrative,
            team_narratives=team_narratives,
            items=items,
        )

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
