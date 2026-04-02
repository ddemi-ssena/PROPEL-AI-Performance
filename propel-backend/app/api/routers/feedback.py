# propel-backend/app/api/routers/feedback.py
# 360° Geri Bildirim Modülü — API Endpoints

from fastapi import APIRouter, Depends, status
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
    - **reviewee_id**: Feedback verilen kişinin employee ID'si
    - **feedback_type**: manager_to_employee / employee_to_manager / peer_to_peer / self_assessment
    - **period_date**: Hangi dönem için (örn: 2024-03-01)
    - Skorlar 1-5 arası (opsiyonel)
    - Metin alanları NLP analizi için kullanılacak
    """
    return FeedbackService.create_feedback(db, feedback_data, current_employee.id)


@router.get(
    "/candidates",
    response_model=List[EmployeeResponse],
    summary="Feedback verilebilecek çalışan listesi"
)
def get_feedback_candidates(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record)
):
    """
    Kullanıcının feedback verebileceği kişileri listeler.
    - Kendi kaydı hariç tutulur
    - Kendi departmanındaki çalışanlar ve yöneticiler döner
    """
    return FeedbackService.get_feedback_candidates(db, current_employee.id)


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
    Kendi feedback özetim — ortalama skorlar ve rozetler.
    Dashboard'da kullanılacak.
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
    - Admin: Herkesi görebilir
    - Manager: Sadece kendi departmanını
    """
    # Admin herkesi görebilir
    if current_user.role == UserRole.admin:
        return FeedbackService.get_feedback_summary(db, employee_id, period_date)

    # Manager sadece kendi departmanını görebilir
    current_employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()
    target_employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not current_employee or not target_employee:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Çalışan bulunamadı")

    if current_user.role == UserRole.department_manager:
        if target_employee.department_id != current_employee.department_id:
            from fastapi import HTTPException
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
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Yetkiniz yok")

    if current_user.role == UserRole.department_manager:
        current_employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()
        if not current_employee or current_employee.department_id != department_id:
            from fastapi import HTTPException
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
        from fastapi import HTTPException
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
    return FeedbackService.update_request_status(
        db, request_id, update_data, current_employee.id
    )


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