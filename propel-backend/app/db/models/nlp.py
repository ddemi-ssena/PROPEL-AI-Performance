from sqlalchemy import Column, Integer, Float, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
import enum

from ..base_class import BaseModel


class NLPSourceType(str, enum.Enum):
    weekly_feedback = "weekly_feedback"
    classic_feedback = "classic_feedback"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SentimentLabel(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class NLPPeriodType(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"


class FeedbackNLPAnalysis(BaseModel):
    __tablename__ = "feedback_nlp_analyses"

    source_type = Column(SQLEnum(NLPSourceType), nullable=False)
    weekly_feedback_id = Column(Integer, ForeignKey("feedback_responses.id"), nullable=True, unique=True)
    classic_feedback_id = Column(Integer, ForeignKey("feedbacks.id"), nullable=True, unique=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewer_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    direction = Column(Text, nullable=True)
    theme = Column(Text, nullable=True)

    analysis_version = Column(Text, nullable=False, default="v1")
    model_provider = Column(Text, nullable=True)
    model_name = Column(Text, nullable=True)

    sentiment_label = Column(SQLEnum(SentimentLabel), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    motivation_score = Column(Float, nullable=True)
    burnout_risk = Column(SQLEnum(RiskLevel), nullable=True)
    flight_risk = Column(SQLEnum(RiskLevel), nullable=True)
    psychological_safety_score = Column(Float, nullable=True)
    collaboration_score = Column(Float, nullable=True)
    growth_signal_score = Column(Float, nullable=True)
    leadership_support_score = Column(Float, nullable=True)

    key_strengths = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    risk_flags = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    support_needs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    keywords = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    manager_summary = Column(Text, nullable=True)
    raw_analysis = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    weekly_feedback = relationship("FeedbackResponse", foreign_keys=[weekly_feedback_id], back_populates="nlp_record")
    classic_feedback = relationship("Feedback", foreign_keys=[classic_feedback_id], back_populates="nlp_record")
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="nlp_analyses")
    reviewer_employee = relationship("Employee", foreign_keys=[reviewer_employee_id])
    department = relationship("Department")

    __table_args__ = (
        UniqueConstraint("source_type", "weekly_feedback_id", name="uq_feedback_nlp_weekly_source"),
        UniqueConstraint("source_type", "classic_feedback_id", name="uq_feedback_nlp_classic_source"),
    )


class EmployeeNLPProfile(BaseModel):
    __tablename__ = "employee_nlp_profiles"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    period_type = Column(SQLEnum(NLPPeriodType), nullable=False)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    period_week = Column(Integer, nullable=True)

    feedback_count = Column(Integer, nullable=False, default=0)
    avg_sentiment_score = Column(Float, nullable=True)
    avg_motivation_score = Column(Float, nullable=True)
    avg_psychological_safety_score = Column(Float, nullable=True)
    avg_collaboration_score = Column(Float, nullable=True)
    avg_growth_signal_score = Column(Float, nullable=True)

    burnout_risk_level = Column(SQLEnum(RiskLevel), nullable=True)
    flight_risk_level = Column(SQLEnum(RiskLevel), nullable=True)

    top_strengths = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    top_risk_areas = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    top_support_needs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    manager_summary = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="nlp_profiles")
    department = relationship("Department")

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "period_type",
            "period_year",
            "period_month",
            "period_week",
            name="uq_employee_nlp_profile_period",
        ),
    )
