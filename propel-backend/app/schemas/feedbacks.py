from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from app.db.models.feedback import FeedbackDirection
from app.schemas.feedback import BadgeResponse
from app.schemas.employee import EmployeeResponse
from app.schemas.nlp import EmployeeNLPProfileResponse, EmployeeNLPReviewResponse, FeedbackNLPAnalysisResponse


class CurrentQuestionResponse(BaseModel):
    question_id: int
    week_number: int
    category: str
    direction: FeedbackDirection
    question_text: str
    is_ai_generated: bool


class SubmitFeedbackPayload(BaseModel):
    receiver_id: int = Field(..., description="Feedback alacak employee ID")
    response_text: str = Field(..., min_length=2, max_length=2000)
    score_communication: float = Field(..., ge=1, le=5)
    score_teamwork: float = Field(..., ge=1, le=5)
    score_leadership: float = Field(..., ge=1, le=5)
    score_technical: float = Field(..., ge=1, le=5)


class NLPTestAnalysisPayload(BaseModel):
    response_text: str = Field(..., min_length=2, max_length=2000)
    question_text: str = Field(
        default=(
            "Bu hafta ekip icinde motivasyon, destek ihtiyaci veya risk sinyali "
            "gosteren somut davranisi ve etkisini hangi ornekle aciklarsin?"
        ),
        max_length=500,
    )
    department_id: Optional[int] = None
    target_role: str = Field(default="employee", pattern="^(admin|department_manager|employee)$")
    week_theme: str = Field(default="Motivasyon & Psikolojik Durum", max_length=100)
    direction_label: str = Field(default="Akran geri bildirimi", max_length=100)
    score_communication: float = Field(default=3, ge=1, le=5)
    score_teamwork: float = Field(default=3, ge=1, le=5)
    score_leadership: float = Field(default=3, ge=1, le=5)
    score_technical: float = Field(default=3, ge=1, le=5)


class NLPTestAnalysisResponse(BaseModel):
    department_name: str
    model_provider: str
    model_name: str
    analysis: Dict[str, Any]


class SubmitFeedbackResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    question_id: int
    response_text: str
    score_communication: float
    score_teamwork: float
    score_leadership: float
    score_technical: float
    nlp_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WeeklyProgressResponse(BaseModel):
    week_number: int
    required_count: int
    completed_count: int
    remaining_count: int
    is_completed: bool


class WeeklyAssignmentTargetResponse(BaseModel):
    id: int
    status: str
    assignment_type: str
    employee: EmployeeResponse


class WeeklyAssignmentStateResponse(BaseModel):
    week_number: int
    required_count: int
    completed_count: int
    remaining_count: int
    is_completed: bool
    current_slot: str
    assignment_required: bool
    mandatory_assignment: Optional[WeeklyAssignmentTargetResponse] = None
    available_candidates: List[EmployeeResponse] = Field(default_factory=list)
    department_candidates: List[EmployeeResponse] = Field(default_factory=list)
    cross_functional_candidates: List[EmployeeResponse] = Field(default_factory=list)
    rules_summary: List[str] = Field(default_factory=list)


class WeeklyNLPInsightResponse(BaseModel):
    profile: EmployeeNLPProfileResponse
    recent_analyses: List[FeedbackNLPAnalysisResponse] = Field(default_factory=list)
    human_review: Optional[EmployeeNLPReviewResponse] = None


class DepartmentWeeklyNLPResponse(BaseModel):
    department_id: int
    period_year: int
    period_month: int
    period_week: int
    employee_count: int
    analyzed_employee_count: int
    avg_sentiment_score: Optional[float] = None
    avg_motivation_score: Optional[float] = None
    avg_psychological_safety_score: Optional[float] = None
    avg_collaboration_score: Optional[float] = None
    avg_growth_signal_score: Optional[float] = None
    high_burnout_count: int
    high_flight_risk_count: int
    top_strengths: List[str] = Field(default_factory=list)
    top_risk_areas: List[str] = Field(default_factory=list)
    top_support_needs: List[str] = Field(default_factory=list)
    headline: str
    recommended_action: Optional[str] = None


class RiskDriver(BaseModel):
    label: str
    evidence: str
    count: Optional[int] = None
    severity: Optional[str] = None


class SummaryMetric(BaseModel):
    label: str
    value: Optional[float] = None
    display_value: str
    risk_level: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    drivers: List[RiskDriver] = Field(default_factory=list)
    description: Optional[str] = None


class SummarySection(BaseModel):
    title: str
    items: List[str] = Field(default_factory=list)


class Employee360SummaryReportResponse(BaseModel):
    employee_id: int
    employee_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    period_year: int
    period_month: int
    period_week: int
    report_title: str
    report_summary: str
    recommended_action: Optional[str] = None
    badges: List[BadgeResponse] = Field(default_factory=list)
    metrics: List[SummaryMetric] = Field(default_factory=list)
    sections: List[SummarySection] = Field(default_factory=list)


class Department360SummaryReportResponse(BaseModel):
    department_id: int
    department_name: str
    period_year: int
    period_month: int
    period_week: int
    report_title: str
    report_summary: str
    recommended_action: Optional[str] = None
    metrics: List[SummaryMetric] = Field(default_factory=list)
    sections: List[SummarySection] = Field(default_factory=list)


class TrendPoint(BaseModel):
    label: str
    value: float


class DistributionPoint(BaseModel):
    label: str
    value: int


class ThemePoint(BaseModel):
    label: str
    value: int


class DepartmentNLPChartsResponse(BaseModel):
    department_id: int
    department_name: str
    period_year: int
    period_month: int
    motivation_trend: List[TrendPoint] = Field(default_factory=list)
    psychological_safety_trend: List[TrendPoint] = Field(default_factory=list)
    flight_risk_distribution: List[DistributionPoint] = Field(default_factory=list)
    burnout_risk_distribution: List[DistributionPoint] = Field(default_factory=list)
    top_risk_themes: List[ThemePoint] = Field(default_factory=list)


class EmployeeMonthlyDeepAnalysisResponse(BaseModel):
    employee_id: int
    employee_name: str
    period_year: int
    period_month: int
    feedback_count: int
    motivation_trend_direction: str
    sentiment_trend_direction: str
    top_complaint_topics: List[str] = Field(default_factory=list)
    top_praise_topics: List[str] = Field(default_factory=list)
    top_themes: List[str] = Field(default_factory=list)
    flight_risk_score: Optional[float] = None
    flight_risk_reasons: List[str] = Field(default_factory=list)
    burnout_risk_level: Optional[str] = None
    burnout_risk_drivers: List[RiskDriver] = Field(default_factory=list)
    burnout_risk_evidence: List[str] = Field(default_factory=list)
    action_recommendation: Optional[str] = None


class DepartmentMonthlyDeepAnalysisResponse(BaseModel):
    department_id: int
    department_name: str
    period_year: int
    period_month: int
    analyzed_feedback_count: int
    analyzed_employee_count: int
    motivation_trend_direction: str
    sentiment_trend_direction: str
    avg_flight_risk_score: Optional[float] = None
    top_complaint_topics: List[str] = Field(default_factory=list)
    top_praise_topics: List[str] = Field(default_factory=list)
    top_themes: List[str] = Field(default_factory=list)
    top_flight_risk_reasons: List[str] = Field(default_factory=list)
    action_recommendation: Optional[str] = None


class EmployeeMonthlyRAGReportResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    employee_id: int
    employee_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    team: Optional[str] = None
    period_year: int
    period_month: int
    report_summary: str
    trend_summary: str
    flight_risk_score: Optional[float] = None
    retention_risk_level: Optional[str] = None
    top_complaint_topics: List[str] = Field(default_factory=list)
    top_praise_topics: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    action_recommendation: Optional[str] = None
    retrieved_memory_count: int = 0
    retrieved_memory_summaries: List[str] = Field(default_factory=list)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    confidence: Optional[float] = None


class DepartmentMonthlyRAGReportResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    department_id: int
    department_name: str
    period_year: int
    period_month: int
    report_summary: str
    trend_summary: str
    flight_risk_score: Optional[float] = None
    retention_risk_level: Optional[str] = None
    top_complaint_topics: List[str] = Field(default_factory=list)
    top_praise_topics: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    action_recommendation: Optional[str] = None
    retrieved_memory_count: int = 0
    retrieved_memory_summaries: List[str] = Field(default_factory=list)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    confidence: Optional[float] = None
