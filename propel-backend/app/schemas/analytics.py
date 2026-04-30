from datetime import date
from typing import Optional

from pydantic import BaseModel


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


class SoftwareModelTrainRequest(BaseModel):
    upload_id: int
    target_column: str = "performance_band"
    model_name: str = "random_forest"
    test_period_count: int = 12


class SoftwareModelTrainResponse(BaseModel):
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
    summary_payload: dict
