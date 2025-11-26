from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from ..base_class import BaseModel

class Department(BaseModel):
    __tablename__ = "departments"
    
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    employees = relationship("Employee", back_populates="department")
    kpis = relationship("KPI", back_populates="department")