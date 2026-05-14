from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from app.analytics.training.sales import SalesTrainingResult


DEFAULT_SALES_ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "artifacts_store" / "sales"


@dataclass
class SalesModelArtifact:
    target_column: str
    model_name: str
    artifact_dir: Path
    model_path: Path
    metadata_path: Path
    metadata: dict[str, Any]
    pipeline: Pipeline


class SalesArtifactStore:
    def __init__(self, root_dir: Path | str = DEFAULT_SALES_ARTIFACT_ROOT):
        self.root_dir = Path(root_dir)

    def _target_dir(self, target_column: str) -> Path:
        return self.root_dir / target_column

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)

    def _latest_pointer_path(self, target_column: str) -> Path:
        return self._target_dir(target_column) / "latest.json"

    def latest_metadata(self, target_column: str) -> dict[str, Any]:
        artifact_dir = self._resolve_artifact_dir(target_column)
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            return {}
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    def _resolve_artifact_dir(self, target_column: str) -> Path:
        target_dir = self._target_dir(target_column)
        latest_path = self._latest_pointer_path(target_column)
        if latest_path.exists():
            try:
                pointer = json.loads(latest_path.read_text(encoding="utf-8"))
                run_id = str(pointer.get("run_id") or "").strip()
                if run_id:
                    return target_dir / "runs" / run_id
            except json.JSONDecodeError:
                pass
        return target_dir

    def save_training_result(
        self,
        result: SalesTrainingResult,
        upload_id: int | None = None,
    ) -> SalesModelArtifact:
        target_dir = self._target_dir(result.target_column)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + f"-{uuid.uuid4().hex[:8]}"
        artifact_dir = target_dir / "runs" / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        model_path = artifact_dir / "model.joblib"
        metadata_path = artifact_dir / "metadata.json"

        metadata = {
            "department": "sales",
            "upload_id": upload_id,
            "run_id": run_id,
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
        self._atomic_write_text(
            metadata_path,
            json.dumps(metadata, ensure_ascii=False, indent=2),
        )
        self._atomic_write_text(
            self._latest_pointer_path(result.target_column),
            json.dumps(
                {
                    "run_id": run_id,
                    "artifact_dir": str(artifact_dir),
                    "metadata_path": str(metadata_path),
                    "trained_at": metadata["trained_at"],
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        return SalesModelArtifact(
            target_column=result.target_column,
            model_name=result.model_name,
            artifact_dir=artifact_dir,
            model_path=model_path,
            metadata_path=metadata_path,
            metadata=metadata,
            pipeline=result.pipeline,
        )

    def load(self, target_column: str) -> SalesModelArtifact:
        artifact_dir = self._resolve_artifact_dir(target_column)
        model_path = artifact_dir / "model.joblib"
        metadata_path = artifact_dir / "metadata.json"

        if not model_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Sales model artifact bulunamadi: {artifact_dir}")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        pipeline = joblib.load(model_path)

        return SalesModelArtifact(
            target_column=target_column,
            model_name=metadata.get("model_name", "unknown"),
            artifact_dir=artifact_dir,
            model_path=model_path,
            metadata_path=metadata_path,
            metadata=metadata,
            pipeline=pipeline,
        )
