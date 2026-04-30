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
from app.schemas.analytics import SoftwareModelTrainResponse, SoftwarePredictionResponse


UPLOAD_DIR = Path("uploads")
SUPPORTED_TARGETS = {"performance_band", "attrition_risk_band"}
SUPPORTED_MODELS = {"logistic_regression", "random_forest", "hist_gradient_boosting"}


class SoftwareMLService:
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
            artifact = SoftwareArtifactStore().save_training_result(result)
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
    ) -> SoftwarePredictionResponse:
        if target_column not in SUPPORTED_TARGETS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen target_column: {target_column}")

        upload = SoftwareMLService._resolve_upload(db, upload_id)
        rows = SoftwareMLService._load_rows(SoftwareMLService._upload_path(upload))
        employee_rows = [row for row in rows if str(row.get("employee_id")) == str(employee_id)]
        if not employee_rows:
            raise HTTPException(status_code=404, detail=f"Upload icinde employee_id bulunamadi: {employee_id}")

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

        return SoftwarePredictionResponse(
            department=prediction.department,
            upload_id=upload_id,
            employee_id=employee_id,
            target_column=prediction.target_column,
            predicted_band=prediction.predicted_band,
            confidence=prediction.confidence,
            probabilities=prediction.probabilities,
            top_features=prediction.top_features,
            summary_payload=prediction.summary_payload,
        )
