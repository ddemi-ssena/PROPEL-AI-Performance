from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

# Employee bilgisi
class EmployeeInSurvey(BaseModel):
    id: int
    position: Optional[str]
    user_id: int
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SurveyResponseBase(BaseModel):
    employee_id: int
    survey_type: str = Field(..., description="motivation, satisfaction, stress")
    score: float = Field(..., ge=1, le=5, description="1-5 arası Likert ölçeği")
    period_date: date
    comments: Optional[str] = Field(None, max_length=500)

class SurveyResponseCreate(SurveyResponseBase):
    pass

class SurveyResponseUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=500)

class SurveyResponseResponse(SurveyResponseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Detaylı response (employee ilişkisiyle)
class SurveyResponseDetailResponse(SurveyResponseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    employee: EmployeeInSurvey
    
    # KUTUP Pulse AI fields
    raw_data: Optional[dict] = None
    mte_score: Optional[float] = None
    ars_score: Optional[float] = None
    
    class Config:
        from_attributes = True

# Weekly Pulse Gelen İstek Şeması
class WeeklyPulseCreate(BaseModel):
    employee_id: int
    period_date: date
    # Sayısal Değerlendirme (1-5)
    q1: int = Field(..., ge=1, le=5)
    q2: int = Field(..., ge=1, le=5)
    q3: int = Field(..., ge=1, le=5)
    # Açık Uçlu NLP Değerlendirmesi
    q4: str = Field(...)
    q5: str = Field(...)
    q6: str = Field(...)