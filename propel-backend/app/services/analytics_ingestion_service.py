from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.analytics.importers import SoftwareKPIImportService


class AnalyticsIngestionService:
    @staticmethod
    async def _load_rows(file: UploadFile) -> list[dict[str, Any]]:
        content = await file.read()
        ext = file.filename.rsplit(".", 1)[-1].lower()

        if ext == "csv":
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in reader]

        if ext == "xlsx":
            try:
                import pandas as pd
            except ImportError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Excel dosyalari icin gerekli pandas kutuphanesi kurulu degil.",
                ) from exc

            df = pd.read_excel(io.BytesIO(content))
            return df.to_dict(orient="records")

        if ext == "json":
            payload = json.loads(content.decode("utf-8"))
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return [payload]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON icerigi liste veya nesne formatinda olmali.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Desteklenmeyen dosya uzantisi: .{ext}",
        )

    @staticmethod
    def load_rows_from_path(file_path: str | Path) -> list[dict[str, Any]]:
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")

        if ext == "csv":
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                return [dict(row) for row in reader]

        if ext == "xlsx":
            try:
                import pandas as pd
            except ImportError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Excel dosyalari icin gerekli pandas kutuphanesi kurulu degil.",
                ) from exc

            df = pd.read_excel(path)
            return df.to_dict(orient="records")

        if ext == "json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return [payload]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON icerigi liste veya nesne formatinda olmali.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Desteklenmeyen dosya uzantisi: .{ext}",
        )

    @staticmethod
    def import_kpi_rows(
        db: Session,
        rows: list[dict[str, Any]],
        department_key: str,
    ) -> dict[str, Any]:
        normalized_department = (department_key or "").strip().lower()

        if normalized_department == "software":
            return SoftwareKPIImportService.import_rows(db, rows)

        if normalized_department == "sales":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Satis departmani importer'i icin veri adapter'i henuz eklenmedi. Analytics omurgasi hazir, mapper siradaki sprintte baglanacak.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Desteklenmeyen departman anahtari: {department_key}",
        )

    @staticmethod
    async def import_kpi_dataset(
        db: Session,
        file: UploadFile,
        department_key: str,
    ) -> dict[str, Any]:
        rows = await AnalyticsIngestionService._load_rows(file)
        return AnalyticsIngestionService.import_kpi_rows(db, rows, department_key)
