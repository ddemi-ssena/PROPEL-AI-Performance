from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..base_class import BaseModel

class Employee(BaseModel):
    __tablename__ = "employees"
    
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position = Column(String(255), nullable=True)
    hire_date = Column(Date, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    kpi_records = relationship("KPIRecord", back_populates="employee")
    survey_responses = relationship("SurveyResponse", back_populates="employee")