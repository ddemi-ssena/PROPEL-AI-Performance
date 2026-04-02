from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..base_class import BaseModel

#User'dan ayrı bir profildir. Çalışanın İK verilerini (position, hire_date) ve performans kayıtlarını tutar. user_id ile User tablosuna bağlıdır.
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
    # Mevcut dosyanın sonuna, kpi_records ve survey_responses'tan SONRA ekle:

    given_feedbacks    = relationship("Feedback", foreign_keys="Feedback.reviewer_id", back_populates="reviewer")
    received_feedbacks = relationship("Feedback", foreign_keys="Feedback.reviewee_id", back_populates="reviewee")
    sent_requests      = relationship("FeedbackRequest", foreign_keys="FeedbackRequest.requester_id", back_populates="requester")
    received_requests  = relationship("FeedbackRequest", foreign_keys="FeedbackRequest.target_id",    back_populates="target")
    badges             = relationship("EmployeeBadge", back_populates="employee")
    nlp_analyses       = relationship("FeedbackNLPAnalysis", foreign_keys="FeedbackNLPAnalysis.employee_id", back_populates="employee")
    nlp_profiles       = relationship("EmployeeNLPProfile", back_populates="employee")
