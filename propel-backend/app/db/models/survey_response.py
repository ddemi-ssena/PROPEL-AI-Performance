from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String, JSON
from sqlalchemy.orm import relationship
from ..base_class import BaseModel

class SurveyResponse(BaseModel):
    __tablename__ = "survey_responses"
    
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    survey_type = Column(String(100), nullable=False)  # motivation, satisfaction, stress, weekly_pulse
    score = Column(Float, nullable=False)  # 1-5 arası Likert
    period_date = Column(Date, nullable=False)
    comments = Column(String(500), nullable=True)

    # Weekly Pulse ML Scores & Raw Data
    raw_data = Column(JSON, nullable=True)
    mte_score = Column(Float, nullable=True)
    ars_score = Column(Float, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="survey_responses")