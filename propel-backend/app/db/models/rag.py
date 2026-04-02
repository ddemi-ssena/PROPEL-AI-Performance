from sqlalchemy import Column, Integer, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
import enum

from ..base_class import BaseModel


class FeedbackMemorySourceType(str, enum.Enum):
    weekly_feedback = "weekly_feedback"
    classic_feedback = "classic_feedback"


class FeedbackMemoryChunk(BaseModel):
    __tablename__ = "feedback_memory_chunks"

    source_type = Column(SQLEnum(FeedbackMemorySourceType), nullable=False)
    weekly_feedback_id = Column(Integer, ForeignKey("feedback_responses.id"), nullable=True, unique=True)
    classic_feedback_id = Column(Integer, ForeignKey("feedbacks.id"), nullable=True, unique=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewer_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    content_text = Column(Text, nullable=False)
    content_summary = Column(Text, nullable=True)
    theme_labels = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    metadata_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    embedding_provider = Column(Text, nullable=False, default="hash")
    embedding_model = Column(Text, nullable=False, default="hash-v1")
    embedding_dimension = Column(Integer, nullable=False, default=128)
    embedding_vector = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)

    weekly_feedback = relationship("FeedbackResponse", foreign_keys=[weekly_feedback_id])
    classic_feedback = relationship("Feedback", foreign_keys=[classic_feedback_id])
    employee = relationship("Employee", foreign_keys=[employee_id])
    reviewer_employee = relationship("Employee", foreign_keys=[reviewer_employee_id])
    department = relationship("Department")

    __table_args__ = (
        UniqueConstraint("source_type", "weekly_feedback_id", name="uq_feedback_memory_weekly_source"),
        UniqueConstraint("source_type", "classic_feedback_id", name="uq_feedback_memory_classic_source"),
    )
