from sqlalchemy import Column, String, Text, Float, Integer, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from ..base_class import BaseModel

class KPIUnit(str, enum.Enum):
    numeric = "numeric"
    percentage = "percentage"
    currency = "currency"
    hours = "hours"

class KPI(BaseModel):
    __tablename__ = "kpis"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(SQLEnum(KPIUnit), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # NULL = genel KPI
    target_value = Column(Float, nullable=True)
    
    # Relationships
    department = relationship("Department", back_populates="kpis")
    records = relationship("KPIRecord", back_populates="kpi")

class KPIRecord(BaseModel):
    __tablename__ = "kpi_records"
    
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    value = Column(Float, nullable=False)
    period_date = Column(Date, nullable=False)
    
    # Relationships
    kpi = relationship("KPI", back_populates="records")
    employee = relationship("Employee", back_populates="kpi_records")