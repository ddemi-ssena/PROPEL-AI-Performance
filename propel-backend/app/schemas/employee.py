from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class UserInEmployee(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class DepartmentInEmployee(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    user_id: int
    department_id: int
    external_employee_code: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    experience_years: Optional[float] = None
    hire_date: Optional[date] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    department_id: Optional[int] = None
    external_employee_code: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    experience_years: Optional[float] = None
    hire_date: Optional[date] = None


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: UserInEmployee
    department: DepartmentInEmployee

    latest_mte: Optional[float] = None
    latest_ars: Optional[float] = None
    latest_ms: Optional[float] = None
    risk_level: Optional[str] = "Low"

    class Config:
        from_attributes = True


class EmployeeSimple(BaseModel):
    id: int
    external_employee_code: Optional[str]
    team: Optional[str]
    position: Optional[str]
    experience_years: Optional[float]
    hire_date: Optional[date]
    user_id: int
    department_id: int

    class Config:
        from_attributes = True


class TeamHealthStat(BaseModel):
    key: str
    label: str
    value: str
    hint: str
    tone: str


class TeamHealthSourceSummary(BaseModel):
    kpi_analyzed_count: int = 0
    pulse_response_count: int = 0
    feedback_profile_count: int = 0
    latest_kpi_period: Optional[date] = None
    latest_pulse_period: Optional[date] = None
    latest_feedback_update: Optional[datetime] = None


class TeamHealthMember(BaseModel):
    id: int
    name: str
    role: str
    team: Optional[str] = None
    external_employee_code: Optional[str] = None
    latest_pulse_score: Optional[float] = None
    latest_mte: Optional[float] = None
    latest_ars: Optional[float] = None
    kpi_score: Optional[float] = None
    kpi_trend: Optional[float] = None
    kpi_latest_period: Optional[date] = None
    feedback_count: int = 0
    feedback_sentiment_score: Optional[float] = None
    feedback_motivation_score: Optional[float] = None
    feedback_flight_risk_level: Optional[str] = None
    feedback_burnout_risk_level: Optional[str] = None
    combined_risk_score: float
    combined_risk_level: str
    recommended_action: str
    data_sources: list[str] = []


class TeamHealthResponse(BaseModel):
    generated_at: datetime
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    member_count: int
    stats: list[TeamHealthStat]
    source_summary: TeamHealthSourceSummary
    members: list[TeamHealthMember]
