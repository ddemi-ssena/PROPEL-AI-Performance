from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_current_active_admin
from app.db.models.data_upload import DataUpload
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.data_upload import DataUploadResponse
from app.services.upload_service import UploadService

router = APIRouter()


@router.post('/', response_model=DataUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_data(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    return await UploadService.process_upload(db, file, file_type, current_user)


@router.get('/', response_model=List[DataUploadResponse])
def list_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    return UploadService.get_all_uploads(db, skip, limit)


@router.get('/{upload_id}', response_model=DataUploadResponse)
def get_upload_detail(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail='Yukleme kaydi bulunamadi')
    return upload
