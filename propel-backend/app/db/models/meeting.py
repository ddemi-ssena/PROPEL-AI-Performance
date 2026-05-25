from sqlalchemy import Column, Date, ForeignKey, Integer, JSON, String, Text, Time
from sqlalchemy.orm import relationship

from ..base_class import BaseModel


class Meeting(BaseModel):
    __tablename__ = "meetings"

    title = Column(String(255), nullable=False)
    team = Column(String(100), nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=45)
    meeting_url = Column(String(1000), nullable=True)
    note = Column(Text, nullable=True)
    agenda_items = Column(JSON, nullable=False, default=list)
    source = Column(String(80), nullable=False, default="team_risk_analysis")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    attendees = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="meeting", cascade="all, delete-orphan")


class MeetingAttendee(BaseModel):
    __tablename__ = "meeting_attendees"

    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    dataset_employee_id = Column(Integer, nullable=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)

    meeting = relationship("Meeting", back_populates="attendees")
    employee = relationship("Employee")
    notification = relationship("Notification", foreign_keys=[notification_id])


class Notification(BaseModel):
    __tablename__ = "notifications"

    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipient_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    recipient_label = Column(String(255), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="in_app")
    status = Column(String(50), nullable=False, default="created")
    notification_type = Column(String(80), nullable=False, default="meeting_invite")
    read_at = Column(String(50), nullable=True)

    meeting = relationship("Meeting", back_populates="notifications")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    recipient_employee = relationship("Employee", foreign_keys=[recipient_employee_id])
