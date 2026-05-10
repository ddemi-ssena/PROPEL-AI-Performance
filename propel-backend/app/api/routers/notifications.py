from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.employee import Employee
from app.db.models.meeting import Notification
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.schemas.meeting import NotificationResponse, TeamReportShareRequest, TeamReportShareResponse

router = APIRouter()


@router.get("/me", response_model=list[NotificationResponse])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    query = db.query(Notification).filter(Notification.recipient_user_id == current_user.id)
    if employee:
        query = query.union(
            db.query(Notification).filter(Notification.recipient_employee_id == employee.id)
        )
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@router.post("/team-report", response_model=TeamReportShareResponse)
def share_team_report(
    payload: TeamReportShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipients: dict[int, tuple[User, Employee | None, str]] = {}

    if payload.include_admins:
        for user in db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True)).all():
            recipients[user.id] = (user, None, "Admin")

    if payload.include_department_managers:
        for user in db.query(User).filter(User.role == UserRole.department_manager, User.is_active.is_(True)).all():
            employee = db.query(Employee).filter(Employee.user_id == user.id).first()
            recipients[user.id] = (user, employee, "Departman yoneticisi")

    if payload.include_team_leads:
        lead_employees = (
            db.query(Employee)
            .join(User, User.id == Employee.user_id)
            .filter(
                Employee.team == payload.team,
                User.is_active.is_(True),
                Employee.position.ilike("%lead%"),
            )
            .all()
        )
        for employee in lead_employees:
            if employee.user:
                recipients[employee.user.id] = (employee.user, employee, "Takim lideri")

    notifications: list[Notification] = []
    body = (
        f"{payload.team} takim analiz raporu paylasildi. "
        f"Ozet: {payload.summary}"
    )
    for user, employee, role_label in recipients.values():
        notification = Notification(
            recipient_user_id=user.id,
            recipient_employee_id=employee.id if employee else None,
            recipient_label=f"{user.full_name} ({role_label})",
            title=payload.report_title,
            body=body,
            channel="in_app",
            status="created",
            notification_type="team_report",
        )
        db.add(notification)
        notifications.append(notification)

    db.commit()
    for notification in notifications:
        db.refresh(notification)

    return TeamReportShareResponse(
        team=payload.team,
        notification_count=len(notifications),
        recipients=notifications,
    )
