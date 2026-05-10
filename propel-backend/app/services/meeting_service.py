from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.employee import Employee
from app.db.models.meeting import Meeting, MeetingAttendee, Notification
from app.db.models.user import User
from app.schemas.meeting import TeamMeetingCreateRequest, TeamMeetingCreateResponse


class MeetingService:
    @staticmethod
    def create_team_meeting(
        db: Session,
        payload: TeamMeetingCreateRequest,
        current_user: User,
    ) -> TeamMeetingCreateResponse:
        if not payload.attendees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Toplanti icin en az bir katilimci secilmeli.",
            )

        meeting = Meeting(
            title=payload.title,
            team=payload.team,
            scheduled_date=payload.scheduled_date,
            scheduled_time=payload.scheduled_time,
            duration_minutes=payload.duration_minutes,
            note=payload.note,
            agenda_items=payload.agenda_items,
            created_by_user_id=current_user.id,
        )
        db.add(meeting)
        db.flush()

        attendees: list[MeetingAttendee] = []
        notifications: list[Notification] = []
        for attendee_payload in payload.attendees:
            employee = MeetingService._resolve_employee(db, attendee_payload.db_employee_id)
            display_name = attendee_payload.name.strip()
            role = attendee_payload.role
            notification = Notification(
                recipient_user_id=employee.user_id if employee else None,
                recipient_employee_id=employee.id if employee else None,
                recipient_label=display_name,
                meeting_id=meeting.id,
                title=f"{payload.team} takim toplantisi planlandi",
                body=MeetingService._notification_body(payload),
            )
            db.add(notification)
            db.flush()

            attendee = MeetingAttendee(
                meeting_id=meeting.id,
                employee_id=employee.id if employee else None,
                dataset_employee_id=attendee_payload.dataset_employee_id,
                display_name=display_name,
                role=role,
                notification_id=notification.id,
            )
            db.add(attendee)
            attendees.append(attendee)
            notifications.append(notification)

        db.commit()
        db.refresh(meeting)
        for attendee in attendees:
            db.refresh(attendee)
        for notification in notifications:
            db.refresh(notification)

        unresolved_count = sum(1 for attendee in attendees if attendee.employee_id is None)
        return TeamMeetingCreateResponse(
            id=meeting.id,
            team=meeting.team,
            title=meeting.title,
            scheduled_date=meeting.scheduled_date,
            scheduled_time=meeting.scheduled_time,
            duration_minutes=meeting.duration_minutes,
            note=meeting.note,
            agenda_items=meeting.agenda_items or [],
            attendee_count=len(attendees),
            notification_count=len(notifications),
            unresolved_attendee_count=unresolved_count,
            attendees=attendees,
            notifications=notifications,
        )

    @staticmethod
    def _resolve_employee(db: Session, db_employee_id: int | None) -> Employee | None:
        if not db_employee_id:
            return None
        return db.query(Employee).filter(Employee.id == db_employee_id).first()

    @staticmethod
    def _notification_body(payload: TeamMeetingCreateRequest) -> str:
        agenda = "; ".join(item for item in payload.agenda_items[:3] if item)
        agenda_text = f" Gundem: {agenda}." if agenda else ""
        return (
            f"{payload.scheduled_date.isoformat()} {payload.scheduled_time.strftime('%H:%M')} icin "
            f"{payload.duration_minutes} dakikalik toplanti planlandi.{agenda_text}"
        )
