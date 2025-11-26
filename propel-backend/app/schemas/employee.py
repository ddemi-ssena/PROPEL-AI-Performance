from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

# User bilgilerini göstermek için
class UserInEmployee(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    
    class Config:
        from_attributes = True

# Department bilgilerini göstermek için
class DepartmentInEmployee(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    user_id: int
    department_id: int
    position: Optional[str] = None
    hire_date: Optional[date] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    department_id: Optional[int] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None

class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: UserInEmployee
    department: DepartmentInEmployee
    
    class Config:
        from_attributes = True

# Basit liste için (ilişkiler olmadan)
class EmployeeSimple(BaseModel):
    id: int
    position: Optional[str]
    hire_date: Optional[date]
    user_id: int
    department_id: int
    
    class Config:
        from_attributes = True