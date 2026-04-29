from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from app.analytics.training.software import SoftwareTrainingResult


DEFAULT_SOFTWARE_ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "artifacts_store" / "software"


@dataclass
class SoftwareModelArtifact:
    target_column: str
    model_name: str
    artifact_dir: Path
    model_path: Path
    metadata_path: Path
    metadata: dict[str, Any]
    pipeline: Pipeline


class SoftwareArtifactStore:
    def __init__(self, root_dir: Path | str = DEFAULT_SOFTWARE_ARTIFACT_ROOT):
        self.root_dir = Path(root_dir)

    def _target_dir(self, target_column: str) -> Path:
        return self.root_dir / target_column

    def save_training_result(self, result: SoftwareTrainingResult) -> SoftwareModelArtifact:
        artifact_dir = self._target_dir(result.target_column)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        model_path = artifact_dir / "model.joblib"
        metadata_path = artifact_dir / "metadata.json"

        metadata = {
            "department": "software",
            "target_column": result.target_column,
            "model_name": result.model_name,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "train_count": result.train_count,
            "test_count": result.test_count,
            "labels": result.labels,
            "metrics": result.metrics,
            "top_features": result.top_features,
            "validation_summary": result.validation_summary,
        }

        joblib.dump(result.pipeline, model_path)
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return SoftwareModelArtifact(
            target_column=result.target_column,
            model_name=result.model_name,
            artifact_dir=artifact_dir,
            model_path=model_path,
            metadata_path=metadata_path,
            metadata=metadata,
            pipeline=result.pipeline,
        )

    def load(self, target_column: str) -> SoftwareModelArtifact:
        artifact_dir = self._target_dir(target_column)
        model_path = artifact_dir / "model.joblib"
        metadata_path = artifact_dir / "metadata.json"

        if not model_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Software model artifact bulunamadi: {artifact_dir}")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        pipeline = joblib.load(model_path)

        return SoftwareModelArtifact(
            target_column=target_column,
            model_name=metadata.get("model_name", "unknown"),
            artifact_dir=artifact_dir,
            model_path=model_path,
            metadata_path=metadata_path,
            metadata=metadata,
            pipeline=pipeline,
        )
