from typing import Optional

from pydantic import BaseModel, Field


class TeamReportMetric(BaseModel):
    label: str
    value: str


class TeamReportMember(BaseModel):
    employee_id: int
    name: str
    role: Optional[str] = None
    department_code: Optional[str] = None
    risk_score: Optional[int] = None
    predicted_band: str
    risk_level: str
    status: Optional[str] = None
    confidence: float
    top_reason: Optional[str] = None
    action: Optional[str] = None
    motivation_score: Optional[float] = None
    completion_rate: Optional[float] = None
    absence_days: Optional[float] = None


class TeamReportTrendPoint(BaseModel):
    period: str
    date: Optional[str] = None
    risk_score: float
    motivation_avg: Optional[float] = None
    capacity_usage: Optional[float] = None


class TeamReportRiskFactor(BaseModel):
    name: str
    count: int = 1
    severity: str = "medium"
    impact_level: Optional[str] = None
    probability: Optional[int] = None
    priority: Optional[str] = None
    note: Optional[str] = None
    current_state: Optional[str] = None
    target_state: Optional[str] = None
    gap: Optional[str] = None
    affected_people: Optional[str] = None
    expected_result: Optional[str] = None


class TeamReportAction(BaseModel):
    title: str
    reason: Optional[str] = None
    owner: Optional[str] = None
    timeframe: Optional[str] = None
    target_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    expected_impact: Optional[str] = None


class TeamReportExportRequest(BaseModel):
    team: str = Field(..., min_length=1, max_length=120)
    report_date: str
    report_type: str = "Haftalik Risk Analizi"
    metrics: list[TeamReportMetric] = []
    main_issue_title: str
    main_issue_description: str
    main_reason: str
    actions: list[TeamReportAction] = []
    members: list[TeamReportMember] = []
    trend: list[TeamReportTrendPoint] = []
    risk_factors: list[TeamReportRiskFactor] = []
    talking_points: list[str] = []
