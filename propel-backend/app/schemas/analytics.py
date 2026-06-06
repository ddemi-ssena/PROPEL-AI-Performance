from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class AnalyticsLayerResponse(BaseModel):
    key: str
    title: str
    summary: str


class DepartmentAnalyticsConfigResponse(BaseModel):
    key: str
    label: str
    description: str
    readiness_status: str
    supports_live_data: bool
    planned_targets: list[str]
    supported_teams: list[str]
    layers: list[AnalyticsLayerResponse]


class AnalyticsMetricCardResponse(BaseModel):
    key: str
    label: str
    value: str
    tone: str
    hint: str


class TeamAnalyticsSnapshotResponse(BaseModel):
    team: str
    employee_count: int
    average_score: float
    average_trend_delta: Optional[float] = None
    watchlist_count: int


class EmployeeAnalyticsSnapshotResponse(BaseModel):
    employee_id: int
    employee_name: str
    team: Optional[str] = None
    position: Optional[str] = None
    external_employee_code: Optional[str] = None
    latest_score: float
    previous_score: Optional[float] = None
    trend_delta: Optional[float] = None
    strongest_category: Optional[str] = None
    weakest_category: Optional[str] = None
    risk_band: str


class DepartmentAnalyticsOverviewResponse(BaseModel):
    definition: DepartmentAnalyticsConfigResponse
    department_name: str
    selected_team: Optional[str] = None
    selected_employee_id: Optional[int] = None
    latest_period: Optional[date] = None
    metrics: list[AnalyticsMetricCardResponse]
    team_summaries: list[TeamAnalyticsSnapshotResponse]
    employee_summaries: list[EmployeeAnalyticsSnapshotResponse]
    notes: list[str]
    sprint_focus: list[str]


class PerformanceStrengthResponse(BaseModel):
    label: str
    tooltip: str


class PerformanceEmployeeRowResponse(BaseModel):
    employee_id: int
    employee_name: str
    external_employee_code: Optional[str] = None
    department_id: int
    department_name: str
    team: Optional[str] = None
    position: Optional[str] = None
    experience_years: Optional[float] = None
    role_level: str
    kpi_score: Optional[float] = None
    trend: Optional[float] = None
    sparkline_values: list[float] = []
    strength: Optional[PerformanceStrengthResponse] = None
    status: str
    latest_period: Optional[date] = None
    record_count: int = 0
    has_kpi_data: bool = False


class PerformanceTeamSummaryResponse(BaseModel):
    team: str
    employee_count: int
    analyzed_count: int
    average_kpi: Optional[float] = None
    average_trend: Optional[float] = None
    declining_count: int = 0
    top_performer_count: int = 0


class PerformanceRoleSummaryResponse(BaseModel):
    role_level: str
    label: str
    employee_count: int
    analyzed_count: int
    average_kpi: Optional[float] = None
    average_trend: Optional[float] = None
    highest_employee_name: Optional[str] = None
    highest_kpi: Optional[float] = None
    lowest_employee_name: Optional[str] = None
    lowest_kpi: Optional[float] = None


class PerformanceKpiSummaryResponse(BaseModel):
    total_employees: int
    analyzed_employees: int
    team_count: int
    average_kpi: Optional[float] = None
    average_trend: Optional[float] = None
    top_performer_count: int
    declining_count: int
    junior_average: Optional[float] = None
    junior_count: int
    senior_average: Optional[float] = None
    senior_count: int


class PerformanceInsightResponse(BaseModel):
    title: str
    icon: str
    text: str
    tone: str


class PerformanceActionGroupResponse(BaseModel):
    title: str
    items: list[str]


class DepartmentPerformanceSummaryResponse(BaseModel):
    scope_department_id: Optional[int] = None
    scope_team: Optional[str] = None
    latest_period: Optional[date] = None
    summary: PerformanceKpiSummaryResponse
    employees: list[PerformanceEmployeeRowResponse]
    teams: list[PerformanceTeamSummaryResponse]
    roles: list[PerformanceRoleSummaryResponse]
    insights: list[PerformanceInsightResponse]
    risk_people: list[PerformanceEmployeeRowResponse]
    success_people: list[PerformanceEmployeeRowResponse]
    action_groups: list[PerformanceActionGroupResponse]


class SoftwareModelTrainRequest(AnalyticsBaseModel):
    upload_id: int
    target_column: str = "performance_band"
    model_name: str = "stacking_lgbm_xgb_rf_lr"
    test_period_count: int = 12


class SoftwareDatasetResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    status: str
    record_count: int
    upload_date: str
    raw_info: Optional[dict] = None


class SoftwareDatasetEmployeeResponse(BaseModel):
    employee_id: int
    employee_name: Optional[str] = None
    display_label: Optional[str] = None
    external_employee_code: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    row_count: int


class SoftwareModelStateResponse(AnalyticsBaseModel):
    department: str
    upload_id: int
    target_column: str
    target_label: str
    is_trained: bool
    is_current_dataset: bool
    trained_at: Optional[str] = None
    model_name: Optional[str] = None
    train_count: Optional[int] = None
    test_count: Optional[int] = None
    labels: list[str] = []
    metrics: dict = {}
    artifact_dir: Optional[str] = None


class SoftwareModelTrainResponse(AnalyticsBaseModel):
    department: str
    upload_id: int
    target_column: str
    model_name: str
    train_count: int
    test_count: int
    labels: list[str]
    metrics: dict
    top_features: list[dict]
    validation_summary: dict
    artifact_dir: str


class SoftwarePredictionResponse(BaseModel):
    department: str
    upload_id: int
    employee_id: int
    target_column: str
    predicted_band: str
    risk_score: int = 0
    confidence: float
    probabilities: dict[str, float]
    top_features: list[dict]
    risk_summary: str
    top_drivers: list[dict]
    recommended_actions: list[str]
    summary_payload: dict
    narrative: Optional[dict] = None


class SoftwareBulkPredictionResponse(BaseModel):
    department: str
    upload_id: int
    target_column: str
    prediction_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    generated_at: datetime
    department_narrative: Optional[dict] = None
    team_narratives: list[dict] = []
    team_analytics: list[dict] = []
    items: list[SoftwarePredictionResponse]


class SoftwareEmployeeKPIMetricResponse(BaseModel):
    code: str
    label: str
    value: str
    raw_value: Optional[float] = None
    unit: str
    status: str
    tone: str
    bar_pct: float
    hint: str
    category: str


class SoftwareEmployeePerformanceResponse(BaseModel):
    department: str
    upload_id: int
    file_name: str
    employee_id: int
    employee_name: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    period_label: str
    latest_period: Optional[date] = None
    metrics: list[SoftwareEmployeeKPIMetricResponse]
    trend_labels: list[str] = []
    trend_values: list[float] = []
    prediction: Optional[SoftwarePredictionResponse] = None


class SoftwareDepartmentInsightsResponse(BaseModel):
    status: str
    department: str
    upload_id: Optional[int] = None
    period: str
    insights: str
    generated_at: datetime
    source: str
    model: Optional[str] = None
    fallback_used: bool = False
    health_score: Optional[float] = None
    sections: dict = {}
    actions: list[dict] = []


class DepartmentDashboardDepartmentResponse(BaseModel):
    id: int
    name: str
    member_count: int
    team_count: int
    teams: list[str] = Field(default_factory=list)


class DepartmentDashboardCoverageResponse(BaseModel):
    kpi_employee_count: int = 0
    kpi_percentage: float = 0.0
    pulse_response_count: int = 0
    pulse_employee_count: int = 0
    pulse_percentage: float = 0.0
    feedback_response_count: int = 0
    feedback_employee_count: int = 0
    feedback_percentage: float = 0.0
    confidence_score: float = 0.0
    last_kpi_update: Optional[datetime] = None
    last_pulse_update: Optional[date] = None
    last_feedback_update: Optional[datetime] = None


class DepartmentDashboardScoresResponse(BaseModel):
    department_health: float
    execution_score: float
    people_health_score: float
    risk_score: float
    confidence_score: float
    weights: dict[str, float]


class DepartmentDashboardSourceResponse(BaseModel):
    label: str
    score: float
    status: str
    metrics: dict = Field(default_factory=dict)
    details: dict = Field(default_factory=dict)


class DepartmentDashboardInsightResponse(BaseModel):
    type: str
    severity: str
    title: str
    description: str
    recommendation: str
    action: str
    team: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)
    manager_interpretation: Optional[str] = None
    impact: Optional[str] = None
    follow_up_metrics: list[str] = Field(default_factory=list)
    source: str = "deterministic"
    model: Optional[str] = None
    fallback_used: bool = False


class DepartmentDashboardTeamResponse(BaseModel):
    team: str
    member_count: int
    scores: dict[str, float]
    metrics: dict = Field(default_factory=dict)
    status: str
    trend: str


class DepartmentDashboardActionResponse(BaseModel):
    title: str
    description: str
    priority: str
    due_date: str
    owner: str
    source: str


class DepartmentDashboardActionsResponse(BaseModel):
    urgent: list[DepartmentDashboardActionResponse] = Field(default_factory=list)
    this_week: list[DepartmentDashboardActionResponse] = Field(default_factory=list)
    monitoring: list[DepartmentDashboardActionResponse] = Field(default_factory=list)


class DepartmentDashboardAISummaryResponse(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    source: str = "deterministic"
    model: Optional[str] = None
    fallback_used: bool = False


class SoftwareDepartmentDashboardResponse(BaseModel):
    status: str
    department: DepartmentDashboardDepartmentResponse
    period: str
    generated_at: datetime
    upload_id: Optional[int] = None
    coverage: DepartmentDashboardCoverageResponse
    scores: DepartmentDashboardScoresResponse
    sources: dict[str, DepartmentDashboardSourceResponse]
    hybrid_insights: list[DepartmentDashboardInsightResponse] = Field(default_factory=list)
    team_breakdown: list[DepartmentDashboardTeamResponse] = Field(default_factory=list)
    actions: DepartmentDashboardActionsResponse
    ai_summary: DepartmentDashboardAISummaryResponse


# ---------------------------------------------------------------------------
# Sales ML Schemas
# ---------------------------------------------------------------------------

class SalesModelTrainRequest(AnalyticsBaseModel):
    upload_id: int
    target_column: str = "Performance_Drop_Target"
    test_period_count: int = 8


class SalesDatasetResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    status: str
    record_count: int
    upload_date: str
    raw_info: Optional[dict] = None


class SalesDatasetEmployeeResponse(BaseModel):
    employee_id: int
    employee_name: Optional[str] = None
    display_label: Optional[str] = None
    external_employee_code: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    row_count: int


class SalesModelStateResponse(AnalyticsBaseModel):
    department: str
    upload_id: int
    target_column: str
    target_label: str
    is_trained: bool
    is_current_dataset: bool
    trained_at: Optional[str] = None
    model_name: Optional[str] = None
    train_count: Optional[int] = None
    test_count: Optional[int] = None
    labels: list[str] = []
    metrics: dict = {}
    artifact_dir: Optional[str] = None


class SalesModelTrainResponse(AnalyticsBaseModel):
    department: str
    upload_id: int
    target_column: str
    model_name: str
    train_count: int
    test_count: int
    labels: list[str]
    metrics: dict
    top_features: list[dict]
    validation_summary: dict
    artifact_dir: str


class SalesPredictionResponse(BaseModel):
    department: str
    upload_id: int
    employee_id: int
    target_column: str
    predicted_band: str
    confidence: float
    probabilities: dict[str, float]
    risk_score: int | None = None
    top_features: list[dict]
    risk_summary: str
    top_drivers: list[dict]
    recommended_actions: list[str]
    summary_payload: dict
    narrative: Optional[dict] = None


class SalesBulkPredictionResponse(BaseModel):
    department: str
    upload_id: int
    target_column: str
    prediction_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    generated_at: datetime
    department_narrative: Optional[dict] = None
    team_narratives: list[dict] = []
    team_analytics: list[dict] = []
    items: list[SalesPredictionResponse]


# ---------------------------------------------------------------------------
# Sales All-Targets Bulk Response
# ---------------------------------------------------------------------------

class SalesTargetResult(BaseModel):
    predicted_band: str
    confidence: float


class SalesEmployeeAllTargets(BaseModel):
    employee_id: int
    employee_name: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    external_employee_code: Optional[str] = None
    perf_drop: Optional[SalesTargetResult] = None
    burnout: Optional[SalesTargetResult] = None
    resignation: Optional[SalesTargetResult] = None
    high_risk: Optional[SalesTargetResult] = None
    top_drivers: list[dict] = []
    recommended_actions: list[str] = []


class SalesAllTargetsBulkResponse(BaseModel):
    upload_id: int
    employee_count: int
    employees: list[SalesEmployeeAllTargets]
    department_narrative: Optional[dict] = None
    team_analytics: list[dict] = []
    generated_at: str


# ---------------------------------------------------------------------------
# Sales Employee Personal Dashboard
# ---------------------------------------------------------------------------

class SalesKPIMetric(BaseModel):
    code: str
    name: str
    raw_value: Optional[float] = None
    unit: str = "ratio"
    direction: str = "higher_is_better"
    threshold_status: Optional[str] = None
    trend_signal: Optional[str] = None


class SalesWeeklyTrendPoint(BaseModel):
    label: str
    score: float


class SalesEmployeePerformanceResponse(BaseModel):
    employee_id: int
    external_code: Optional[str] = None
    latest_period: Optional[str] = None
    kpis: dict[str, SalesKPIMetric] = {}
    weekly_trend: list[SalesWeeklyTrendPoint] = []
    prediction: Optional[SalesPredictionResponse] = None
    has_upload: bool = False
    has_model: bool = False
