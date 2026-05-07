from datetime import date
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
    department_narrative: Optional[dict] = None
    team_narratives: list[dict] = []
    items: list[SoftwarePredictionResponse]
