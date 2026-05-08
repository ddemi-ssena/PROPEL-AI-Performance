import csv
import json
import logging
import os
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.data_upload import DataUpload
from app.db.models.user import User
from app.services.analytics_ingestion_service import AnalyticsIngestionService


UPLOAD_DIR = "uploads"
logger = logging.getLogger(__name__)


class UploadService:
    @staticmethod
    def get_all_uploads(db: Session, skip: int = 0, limit: int = 100) -> List[DataUpload]:
        return db.query(DataUpload).order_by(DataUpload.upload_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    async def process_upload(
        db: Session,
        file: UploadFile,
        file_type: str,
        user: User,
        department_key: Optional[str] = None,
    ) -> DataUpload:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in [".csv", ".xlsx", ".json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Desteklenmeyen dosya formati: {ext}. Sadece .csv, .xlsx ve .json desteklenir.",
            )

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya boyutu cok buyuk (Maksimum 10MB).",
            )

        db_upload = DataUpload(
            file_name=file.filename,
            file_type=file_type,
            uploaded_by_id=user.id,
            status="Processing",
            raw_info={"department_key": department_key} if department_key else None,
        )
        db.add(db_upload)
        db.commit()
        db.refresh(db_upload)

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{db_upload.id}_{file.filename}")

        try:
            with open(file_path, "wb") as target:
                target.write(await file.read())

            record_count = 0
            import_info = None
            if file_type == "Performans Metrikleri (KPI)" and department_key:
                rows = AnalyticsIngestionService.load_rows_from_path(file_path)
                record_count = len(rows)
                try:
                    import_info = AnalyticsIngestionService.import_kpi_rows(
                        db=db,
                        rows=rows,
                        department_key=department_key,
                    )
                    record_count = int(import_info.get("record_count", record_count))
                except HTTPException as exc:
                    db.rollback()
                    db_upload = db.query(DataUpload).filter(DataUpload.id == db_upload.id).first()
                    import_info = {
                        "department": department_key,
                        "import_status": "Skipped",
                        "import_warning": exc.detail,
                        "raw_row_count": record_count,
                    }
                except Exception as exc:
                    logger.exception(
                        "KPI ingestion failed after upload",
                        extra={"upload_id": db_upload.id, "department_key": department_key},
                    )
                    db.rollback()
                    db_upload = db.query(DataUpload).filter(DataUpload.id == db_upload.id).first()
                    import_info = {
                        "department": department_key,
                        "import_status": "Skipped",
                        "import_warning": type(exc).__name__,
                        "raw_row_count": record_count,
                    }
            elif ext == ".csv":
                with open(file_path, "r", encoding="utf-8-sig", newline="") as source:
                    reader = csv.reader(source)
                    record_count = max(0, sum(1 for _ in reader) - 1)
            elif ext == ".xlsx":
                try:
                    import pandas as pd
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Excel yuklemeleri icin pandas backend ortaminda kurulu degil.",
                    ) from exc
                record_count = len(pd.read_excel(file_path))
            elif ext == ".json":
                with open(file_path, "r", encoding="utf-8") as source:
                    data = json.load(source)
                if isinstance(data, list):
                    record_count = len(data)
                elif isinstance(data, dict):
                    record_count = 1
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="JSON icerigi liste veya nesne formatinda olmali.",
                    )

            db_upload.record_count = max(0, record_count)
            db_upload.status = "Success"
            if import_info:
                db_upload.raw_info = {
                    **(db_upload.raw_info or {}),
                    "import_info": import_info,
                }
            db.commit()

        except HTTPException as exc:
            db_upload.status = "Error"
            db_upload.error_message = str(exc.detail)
            db.commit()
            raise
        except (csv.Error, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            db_upload.status = "Error"
            db_upload.error_message = str(exc)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dosya formati okunamadi veya beklenen semaya uymuyor: {str(exc)}",
            ) from exc
        except Exception as exc:
            logger.exception(
                "Upload processing failed",
                extra={
                    "upload_id": db_upload.id,
                    "file_name": db_upload.file_name,
                    "file_type": db_upload.file_type,
                    "department_key": department_key,
                },
            )
            db_upload.status = "Error"
            db_upload.error_message = type(exc).__name__
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dosya islenirken beklenmeyen bir hata olustu. Log kaydindaki upload_id ile incelenmeli.",
            ) from exc

        return db_upload
