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
