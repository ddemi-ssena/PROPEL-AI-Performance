# propel-backend/app/schemas/feedback.py
# 360° Geri Bildirim Modülü — Pydantic Schemas

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from app.db.models.feedback import FeedbackType, FeedbackStatus, BadgeType, BadgeLevel


# ──────────────────────────────────────────────
# Yardımcı küçük schema'lar (response içinde)
# ──────────────────────────────────────────────

class EmployeeInFeedback(BaseModel):
    """Feedback response'larında çalışan bilgisi"""
    id: int
    position: Optional[str]
    user_id: int
    full_name: Optional[str] = None  # user.full_name buraya taşınacak

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# FEEDBACK SCHEMAS
# ──────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    """Yeni geri bildirim oluştururken gönderilen veri"""

    reviewee_id:   int = Field(..., description="Feedback verilen kişinin employee ID'si")
    feedback_type: FeedbackType
    period_date:   date = Field(..., description="Hangi değerlendirme dönemi (ör: 2024-03-01)")

    # Yapılandırılmış skorlar — hepsi opsiyonel, 1-5 arası
    score_communication:   Optional[float] = Field(None, ge=1, le=5, description="İletişim skoru")
    score_teamwork:        Optional[float] = Field(None, ge=1, le=5, description="Takım çalışması skoru")
    score_problem_solving: Optional[float] = Field(None, ge=1, le=5, description="Problem çözme skoru")
    score_leadership:      Optional[float] = Field(None, ge=1, le=5, description="Liderlik skoru")
    score_technical:       Optional[float] = Field(None, ge=1, le=5, description="Teknik beceri skoru")

    # Serbest metin — NLP için ana hammadde
    strength_text:     Optional[str] = Field(None, max_length=1000, description="En güçlü yönü nedir?")
    improvement_text:  Optional[str] = Field(None, max_length=1000, description="Geliştirebileceği alan?")
    general_comment:   Optional[str] = Field(None, max_length=1000, description="Genel yorum")

    # Seçenekler
    is_anonymous:  bool = Field(False, description="Anonim gönderilsin mi?")
    is_voice_input: bool = Field(False, description="Sesle mi girildi?")

    # Talebe bağlı mı?
    request_id: Optional[int] = Field(None, description="Varsa FeedbackRequest ID'si")


class FeedbackResponse(BaseModel):
    """API'den dönen geri bildirim verisi"""
    id:            int
    reviewer_id:   int
    reviewee_id:   int
    feedback_type: FeedbackType
    period_date:   date

    score_communication:   Optional[float]
    score_teamwork:        Optional[float]
    score_problem_solving: Optional[float]
    score_leadership:      Optional[float]
    score_technical:       Optional[float]

    strength_text:    Optional[str]
    improvement_text: Optional[str]
    general_comment:  Optional[str]

    is_anonymous:   bool
    is_voice_input: bool
    nlp_result:     Optional[dict]  # Aşama 2'de dolacak
    request_id:     Optional[int]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackDetailResponse(FeedbackResponse):
    """İlişkilerle birlikte detaylı feedback — kimin kime verdiği görünür"""
    reviewer: Optional[EmployeeInFeedback] = None
    reviewee: Optional[EmployeeInFeedback] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# FEEDBACK REQUEST SCHEMAS
# ──────────────────────────────────────────────

class FeedbackRequestCreate(BaseModel):
    """Birinden feedback talep etmek için"""
    target_id:   int  = Field(..., description="Feedback istenen kişinin employee ID'si")
    period_date: date
    deadline:    Optional[date] = Field(None, description="Son teslim tarihi")
    message:     Optional[str] = Field(None, max_length=500, description="Talep mesajı")


class FeedbackRequestResponse(BaseModel):
    id:           int
    requester_id: int
    target_id:    int
    status:       FeedbackStatus
    period_date:  date
    deadline:     Optional[date]
    message:      Optional[str]
    created_at:   datetime
    updated_at:   datetime

    class Config:
        from_attributes = True


class FeedbackRequestUpdate(BaseModel):
    """Talep durumunu güncellemek için (kabul/red)"""
    status: FeedbackStatus


# ──────────────────────────────────────────────
# BADGE SCHEMAS
# ──────────────────────────────────────────────

class BadgeResponse(BaseModel):
    id:          int
    employee_id: int
    badge_type:  BadgeType
    badge_level: BadgeLevel
    period_date: date
    created_at:  datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# ÖZET SCHEMA — Dashboard için
# ──────────────────────────────────────────────

class FeedbackSummary(BaseModel):
    """Bir çalışanın feedback özetini döndürür"""
    employee_id:           int
    total_received:        int
    avg_communication:     Optional[float]
    avg_teamwork:          Optional[float]
    avg_problem_solving:   Optional[float]
    avg_leadership:        Optional[float]
    avg_technical:         Optional[float]
    overall_avg:           Optional[float]
    badges:                List[BadgeResponse] = []