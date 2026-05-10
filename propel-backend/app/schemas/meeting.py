from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field


class MeetingAttendeeRequest(BaseModel):
    dataset_employee_id: Optional[int] = None
    db_employee_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=255)


class TeamMeetingCreateRequest(BaseModel):
    team: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = Field(45, ge=15, le=180)
    note: Optional[str] = None
    agenda_items: list[str] = []
    attendees: list[MeetingAttendeeRequest] = []


class MeetingAttendeeResponse(BaseModel):
    id: int
    employee_id: Optional[int] = None
    dataset_employee_id: Optional[int] = None
    display_name: str
    role: Optional[str] = None
    notification_id: Optional[int] = None

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: int
    recipient_user_id: Optional[int] = None
    recipient_employee_id: Optional[int] = None
    recipient_label: str
    meeting_id: Optional[int] = None
    title: str
    body: str
    channel: str
    status: str
    notification_type: str

    model_config = {"from_attributes": True}


class TeamReportShareRequest(BaseModel):
    team: str = Field(..., min_length=1, max_length=100)
    report_title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1)
    include_admins: bool = True
    include_department_managers: bool = True
    include_team_leads: bool = True


class TeamReportShareResponse(BaseModel):
    team: str
    notification_count: int
    recipients: list[NotificationResponse]


class TeamMeetingCreateResponse(BaseModel):
    id: int
    team: str
    title: str
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    note: Optional[str] = None
    agenda_items: list[str]
    attendee_count: int
    notification_count: int
    unresolved_attendee_count: int
    attendees: list[MeetingAttendeeResponse]
    notifications: list[NotificationResponse]

    model_config = {"from_attributes": True}
