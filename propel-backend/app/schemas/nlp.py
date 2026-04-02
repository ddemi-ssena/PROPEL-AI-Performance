from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.db.models.nlp import NLPPeriodType, NLPSourceType, RiskLevel, SentimentLabel


class FeedbackNLPAnalysisBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    source_type: NLPSourceType
    weekly_feedback_id: Optional[int] = None
    classic_feedback_id: Optional[int] = None
    employee_id: int
    reviewer_employee_id: Optional[int] = None
    department_id: Optional[int] = None
    direction: Optional[str] = None
    theme: Optional[str] = None
    analysis_version: str = "v1"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    sentiment_label: Optional[SentimentLabel] = None
    sentiment_score: Optional[float] = None
    motivation_score: Optional[float] = Field(None, ge=1, le=5)
    burnout_risk: Optional[RiskLevel] = None
    flight_risk: Optional[RiskLevel] = None
    psychological_safety_score: Optional[float] = Field(None, ge=1, le=5)
    collaboration_score: Optional[float] = Field(None, ge=1, le=5)
    growth_signal_score: Optional[float] = Field(None, ge=1, le=5)
    leadership_support_score: Optional[float] = Field(None, ge=1, le=5)
    key_strengths: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    support_needs: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    manager_summary: Optional[str] = None
    raw_analysis: Optional[Dict[str, Any]] = None


class FeedbackNLPAnalysisCreate(FeedbackNLPAnalysisBase):
    pass


class FeedbackNLPAnalysisResponse(FeedbackNLPAnalysisBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeNLPProfileBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    employee_id: int
    department_id: Optional[int] = None
    period_type: NLPPeriodType
    period_year: int
    period_month: int = Field(..., ge=1, le=12)
    period_week: Optional[int] = Field(None, ge=1, le=4)
    feedback_count: int = 0
    avg_sentiment_score: Optional[float] = None
    avg_motivation_score: Optional[float] = None
    avg_psychological_safety_score: Optional[float] = None
    avg_collaboration_score: Optional[float] = None
    avg_growth_signal_score: Optional[float] = None
    burnout_risk_level: Optional[RiskLevel] = None
    flight_risk_level: Optional[RiskLevel] = None
    top_strengths: List[str] = Field(default_factory=list)
    top_risk_areas: List[str] = Field(default_factory=list)
    top_support_needs: List[str] = Field(default_factory=list)
    manager_summary: Optional[str] = None
    recommended_action: Optional[str] = None


class EmployeeNLPProfileResponse(EmployeeNLPProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
