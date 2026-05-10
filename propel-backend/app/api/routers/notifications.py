from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.employee import Employee
from app.db.models.meeting import Notification
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.meeting import NotificationResponse

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
