from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DataUploadBase(BaseModel):
    file_name: str
    file_type: str
    record_count: int = 0
    status: str = "Processing"
    error_message: Optional[str] = None

class DataUploadCreate(DataUploadBase):
    uploaded_by_id: int

class DataUploadResponse(DataUploadBase):
    id: int
    upload_date: datetime
    uploaded_by_id: int

    class Config:
        from_attributes = True
