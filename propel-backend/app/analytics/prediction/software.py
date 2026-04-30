from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.analytics.artifacts.software import SoftwareModelArtifact
from app.analytics.features.software import SoftwareFeatureBuilder


@dataclass
class SoftwarePredictionResult:
    department: str
    target_column: str
    predicted_band: str
    confidence: float
    probabilities: dict[str, float]
    top_features: list[dict[str, float]]
    summary_payload: dict[str, Any]


class SoftwarePredictionService:
    @staticmethod
    def predict_latest(
        artifact: SoftwareModelArtifact,
        rows: list[dict[str, Any]],
    ) -> SoftwarePredictionResult:
        if not rows:
            raise ValueError("Prediction icin en az bir satir gerekir.")

        dataset = SoftwareFeatureBuilder.build_from_rows(rows)
        if not dataset.feature_rows:
            raise ValueError("Prediction icin islenebilir feature satiri bulunamadi.")

        latest_index = max(
            range(len(dataset.metadata_rows)),
            key=lambda index: (
                dataset.metadata_rows[index]["year"],
                dataset.metadata_rows[index]["week"],
            ),
        )
        feature_row = dataset.feature_rows[latest_index]
        metadata_row = dataset.metadata_rows[latest_index]

        prediction = artifact.pipeline.predict([feature_row])[0]
        probabilities: dict[str, float] = {}
        confidence = 1.0

        classifier = artifact.pipeline.named_steps.get("classifier")
        if hasattr(artifact.pipeline, "predict_proba"):
            probability_values = artifact.pipeline.predict_proba([feature_row])[0]
            classes = list(getattr(classifier, "classes_", []))
            probabilities = {
                str(label): round(float(probability), 6)
                for label, probability in zip(classes, probability_values)
            }
            confidence = max(probabilities.values()) if probabilities else 1.0

        return SoftwarePredictionResult(
            department="software",
            target_column=artifact.target_column,
            predicted_band=str(prediction),
            confidence=round(float(confidence), 6),
            probabilities=probabilities,
            top_features=artifact.metadata.get("top_features", []),
            summary_payload={
                "employee_id": metadata_row["employee_id"],
                "team": metadata_row.get("team"),
                "role": metadata_row.get("role"),
                "period_date": metadata_row["period_date"],
                "model_name": artifact.model_name,
                "trained_at": artifact.metadata.get("trained_at"),
            },
        )
