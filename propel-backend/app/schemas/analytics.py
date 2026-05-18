from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
    model_name: str = "random_forest"
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
