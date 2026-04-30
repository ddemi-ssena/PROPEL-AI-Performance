from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class AnalyticsLayerDefinition:
    key: str
    title: str
    summary: str


@dataclass(frozen=True)
class DepartmentAnalyticsDefinition:
    key: str
    label: str
    description: str
    readiness_status: str
    supports_live_data: bool
    planned_targets: list[str] = field(default_factory=list)
    supported_teams: list[str] = field(default_factory=list)
    layers: list[AnalyticsLayerDefinition] = field(default_factory=list)


@dataclass(frozen=True)
class EmployeeAnalyticsSnapshot:
    employee_id: int
    employee_name: str
    team: Optional[str]
    position: Optional[str]
    external_employee_code: Optional[str]
    latest_score: float
    previous_score: Optional[float]
    trend_delta: Optional[float]
    strongest_category: Optional[str]
    weakest_category: Optional[str]
    risk_band: str


@dataclass(frozen=True)
class TeamAnalyticsSnapshot:
    team: str
    employee_count: int
    average_score: float
    average_trend_delta: Optional[float]
    watchlist_count: int


@dataclass(frozen=True)
class OverviewMetricCard:
    key: str
    label: str
    value: str
    tone: str
    hint: str


@dataclass(frozen=True)
class DepartmentAnalyticsOverview:
    definition: DepartmentAnalyticsDefinition
    department_name: str
    selected_team: Optional[str]
    selected_employee_id: Optional[int]
    latest_period: Optional[date]
    metrics: list[OverviewMetricCard]
    team_summaries: list[TeamAnalyticsSnapshot]
    employee_summaries: list[EmployeeAnalyticsSnapshot]
    notes: list[str]
    sprint_focus: list[str]
