import os
import csv
import json
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.services.analytics_ingestion_service import AnalyticsIngestionService
from app.db.models.data_upload import DataUpload
from app.db.models.user import User

UPLOAD_DIR = "uploads"

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
        # Validate extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.csv', '.xlsx', '.json']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Desteklenmeyen dosya formatı: {ext}. Sadece .csv, .xlsx, ve .json desteklenir."
            )

        # Validate size (10MB)
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya boyutu çok büyük (Maksimum 10MB)."
            )

        # Create upload record
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

        # Ensure upload dir exists
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        file_path = os.path.join(UPLOAD_DIR, f"{db_upload.id}_{file.filename}")
        
        try:
            # Save file
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Parse for record count / analytics import
            record_count = 0
            import_info = None
            if file_type == "Performans Metrikleri (KPI)" and department_key:
                file.file.seek(0)
                file.filename = os.path.basename(file_path)
                import_info = await AnalyticsIngestionService.import_kpi_dataset(
                    db=db,
                    file=file,
                    department_key=department_key,
                )
                record_count = int(import_info.get("record_count", 0))
            elif ext == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    record_count = sum(1 for row in reader) - 1 # Exclude header
            elif ext == '.xlsx':
                try:
                    import pandas as pd
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Excel yuklemeleri icin gerekli pandas kutuphanesi backend ortaminda kurulu degil."
                    ) from exc
                df = pd.read_excel(file_path)
                record_count = len(df)
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        record_count = len(data)
                    elif isinstance(data, dict):
                        record_count = 1
            
            # Update record
            db_upload.record_count = max(0, record_count)
            db_upload.status = "Success"
            if import_info:
                db_upload.raw_info = {
                    **(db_upload.raw_info or {}),
                    "import_info": import_info,
                }
            db.commit()

        except Exception as e:
            db_upload.status = "Error"
            db_upload.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dosya işlenirken hata oluştu: {str(e)}"
            )

        return db_upload
