from sqlalchemy import Column, Integer, Float, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint, DateTime, Boolean
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


class NLPReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    false_alarm = "false_alarm"
    follow_up_required = "follow_up_required"


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

    @staticmethod
    def _unit_interval(value) -> float | None:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return round(max(0.0, min(1.0, numeric)), 2)

    def _risk_confidence(self, risk_key: str) -> float | None:
        raw = self.raw_analysis if isinstance(self.raw_analysis, dict) else {}
        explicit = self._unit_interval(raw.get(f"{risk_key}_confidence"))
        if explicit is not None:
            return explicit
        return self._unit_interval(raw.get("confidence"))

    @property
    def burnout_risk_confidence(self) -> float | None:
        return self._risk_confidence("burnout_risk")

    @property
    def flight_risk_confidence(self) -> float | None:
        return self._risk_confidence("flight_risk")


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

    @staticmethod
    def _score_confidence(score: float | None, risk_level: RiskLevel | None, feedback_count: int) -> float | None:
        if score is None or risk_level is None or feedback_count <= 0:
            return None

        if risk_level == RiskLevel.low:
            distance = max(float(score) - 4.0, 0.0) / 1.0
        elif risk_level == RiskLevel.medium:
            distance = min(abs(float(score) - 2.5), abs(float(score) - 4.0)) / 1.5
        else:
            distance = max(2.5 - float(score), 0.0) / 1.5

        evidence = min(feedback_count, 5) / 5
        confidence = 0.35 + (0.35 * evidence) + (0.30 * min(distance, 1.0))
        return round(max(0.0, min(0.95, confidence)), 2)

    @property
    def burnout_risk_confidence(self) -> float | None:
        return self._score_confidence(
            self.avg_motivation_score,
            self.burnout_risk_level,
            self.feedback_count,
        )

    @property
    def flight_risk_confidence(self) -> float | None:
        return self._score_confidence(
            self.avg_psychological_safety_score,
            self.flight_risk_level,
            self.feedback_count,
        )


class EmployeeNLPReview(BaseModel):
    __tablename__ = "employee_nlp_reviews"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    period_type = Column(SQLEnum(NLPPeriodType), nullable=False)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    period_week = Column(Integer, nullable=True)

    status = Column(SQLEnum(NLPReviewStatus), nullable=False, default=NLPReviewStatus.pending)
    note = Column(Text, nullable=True)
    manager_acknowledged = Column(Boolean, nullable=False, default=True)
    reviewed_at = Column(DateTime, nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id])
    reviewer_user = relationship("User", foreign_keys=[reviewer_user_id])
    reviewer_employee = relationship("Employee", foreign_keys=[reviewer_employee_id])
    department = relationship("Department")

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "period_type",
            "period_year",
            "period_month",
            "period_week",
            name="uq_employee_nlp_review_period",
        ),
    )

    @property
    def reviewer_name(self) -> str | None:
        if self.reviewer_user:
            return self.reviewer_user.full_name
        return None
