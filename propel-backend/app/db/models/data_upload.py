from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..base_class import BaseModel

class DataUpload(BaseModel):
    __tablename__ = "data_uploads"

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # e.g., 'KPI', 'Employee', 'Survey'
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    record_count = Column(Integer, default=0)
    status = Column(String(50), default="Processing") # 'Success', 'Error', 'Processing'
    error_message = Column(String(500), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Optional: store raw data or metadata
    raw_info = Column(JSON, nullable=True)
