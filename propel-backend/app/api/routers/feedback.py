# propel-backend/app/api/routers/feedback.py
# 360° Geri Bildirim Modülü — API Endpoints

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.employee import Employee
from app.schemas.employee import EmployeeResponse
from app.schemas.feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackDetailResponse,
    FeedbackRequestCreate, FeedbackRequestResponse, FeedbackRequestUpdate,
    BadgeResponse, FeedbackSummary
)
from app.services.feedback_service import FeedbackService
from app.api.dependencies import get_current_user, get_current_employee_record

router = APIRouter()


# ──────────────────────────────────────────────
# FEEDBACK ENDPOINTS
# ──────────────────────────────────────────────

@router.post(
    "/",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Geri bildirim gönder"
)
def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """
    Bir çalışana 360° geri bildirim gönder.
    """
    return FeedbackService.create_feedback(db, feedback_data, current_employee.id)


@router.get(
    "/candidates",
    response_model=List[EmployeeResponse],
    summary="Feedback verilebilecek çalışan listesi"
)
def get_feedback_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının feedback verebileceği kişileri listeler.
    - Admin: Tüm çalışanları görebilir
    - Manager: Kendi departmanını
    - Employee: Kendi departmanını
    """
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    current_employee_id = current_employee.id if current_employee else -1
    
    query = db.query(Employee).join(Employee.user).filter(
        Employee.id != current_employee_id
    )

    if current_user.role == UserRole.admin:
        return query.order_by(User.role.desc(), User.full_name.asc()).all()

    if not current_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu kullanıcının çalışan kaydı bulunamadı"
        )

    allowed_roles = [UserRole.employee, UserRole.department_manager]
    return query.filter(
        Employee.department_id == current_employee.department_id,
        User.role.in_(allowed_roles)
    ).order_by(User.role.desc(), User.full_name.asc()).all()


@router.get(
    "/received",
    response_model=List[FeedbackDetailResponse],
    summary="Aldığım geri bildirimler"
)
def get_my_received_feedbacks(
    period_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Bana gönderilen tüm geri bildirimleri listele"""
    return FeedbackService.get_received_feedbacks(db, current_employee.id, period_date)


@router.get(
    "/given",
    response_model=List[FeedbackResponse],
    summary="Verdiğim geri bildirimler"
)
def get_my_given_feedbacks(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Benim verdiğim tüm geri bildirimleri listele"""
    return FeedbackService.get_given_feedbacks(db, current_employee.id)


@router.get(
    "/summary/me",
    response_model=FeedbackSummary,
    summary="Kendi feedback özetim"
)
def get_my_feedback_summary(
    period_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """
    Kendi feedback özetim.
    """
    return FeedbackService.get_feedback_summary(db, current_employee.id, period_date)


@router.get(
    "/summary/{employee_id}",
    response_model=FeedbackSummary,
    summary="Çalışanın feedback özeti (manager/admin)"
)
def get_employee_feedback_summary(
    employee_id: int,
    period_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Belirli bir çalışanın feedback özeti.
    """
    if current_user.role == UserRole.admin:
        return FeedbackService.get_feedback_summary(db, employee_id, period_date)

    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if not current_employee or not target_employee:
        raise HTTPException(status_code=404, detail="Çalışan bulunamadı")

    if current_user.role == UserRole.department_manager:
        if target_employee.department_id != current_employee.department_id:
            raise HTTPException(status_code=403, detail="Bu çalışanın verilerine erişim yetkiniz yok")

    return FeedbackService.get_feedback_summary(db, employee_id, period_date)


@router.get(
    "/department/{department_id}",
    response_model=List[FeedbackDetailResponse],
    summary="Departman feedbackleri (manager/admin)"
)
def get_department_feedbacks(
    department_id: int,
    period_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir departmandaki tüm feedbackleri listele"""
    if current_user.role == UserRole.employee:
        raise HTTPException(status_code=403, detail="Yetkiniz yok")

    if current_user.role == UserRole.department_manager:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not current_employee or current_employee.department_id != department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmanınızı görebilirsiniz")

    return FeedbackService.get_department_feedbacks(db, department_id, period_date)


@router.get(
    "/all",
    response_model=List[FeedbackDetailResponse],
    summary="Tüm feedbackler (sadece admin)"
)
def get_all_feedbacks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sistemdeki tüm feedbackleri listele — sadece admin"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Sadece admin erişebilir")
    return FeedbackService.get_all_feedbacks(db, skip, limit)


# ──────────────────────────────────────────────
# FEEDBACK REQUEST ENDPOINTS
# ──────────────────────────────────────────────

@router.post(
    "/requests",
    response_model=FeedbackRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Feedback talep et"
)
def create_feedback_request(
    request_data: FeedbackRequestCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Bir çalışandan feedback talep et"""
    return FeedbackService.create_feedback_request(db, request_data, current_employee.id)


@router.get(
    "/requests/incoming",
    response_model=List[FeedbackRequestResponse],
    summary="Bana gelen feedback talepleri"
)
def get_incoming_requests(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Benden beklenen feedback talepleri"""
    return FeedbackService.get_my_requests(db, current_employee.id)


@router.patch(
    "/requests/{request_id}",
    response_model=FeedbackRequestResponse,
    summary="Talebi kabul et veya reddet"
)
def update_request_status(
    request_id: int,
    update_data: FeedbackRequestUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Gelen feedback talebini kabul et (completed) veya reddet (declined)"""
    return FeedbackService.update_request_status(db, request_id, update_data, current_employee.id)


# ──────────────────────────────────────────────
# BADGE ENDPOINTS
# ──────────────────────────────────────────────

@router.get(
    "/badges/me",
    response_model=List[BadgeResponse],
    summary="Rozetlerim"
)
def get_my_badges(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """Kazandığım rozetleri listele"""
    return FeedbackService.get_employee_badges(db, current_employee.id)


@router.get(
    "/badges/{employee_id}",
    response_model=List[BadgeResponse],
    summary="Çalışanın rozetleri"
)
def get_employee_badges(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir çalışanın rozetlerini görüntüle"""
    return FeedbackService.get_employee_badges(db, employee_id)