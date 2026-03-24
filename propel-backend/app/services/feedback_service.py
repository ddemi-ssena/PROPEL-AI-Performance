# propel-backend/app/services/feedback_service.py
# 360° Geri Bildirim Modülü — İş Mantığı

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import date

from app.db.models.feedback import (
    Feedback, FeedbackRequest, EmployeeBadge,
    FeedbackType, FeedbackStatus
)
from app.db.models.employee import Employee
from app.schemas.feedback import (
    FeedbackCreate, FeedbackRequestCreate,
    FeedbackRequestUpdate, FeedbackSummary, BadgeResponse
)


class FeedbackService:

    # ──────────────────────────────────────────────
    # FEEDBACK — Geri Bildirim Oluştur
    # ──────────────────────────────────────────────

    @staticmethod
    def create_feedback(
        db: Session,
        feedback_data: FeedbackCreate,
        reviewer_employee_id: int
    ) -> Feedback:
        """Yeni geri bildirim oluştur"""

        # Kendine feedback vermeyi engelle
        if feedback_data.reviewee_id == reviewer_employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kendinize geri bildirim veremezsiniz"
            )

        # Reviewee var mı?
        reviewee = db.query(Employee).filter(
            Employee.id == feedback_data.reviewee_id
        ).first()
        if not reviewee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {feedback_data.reviewee_id})"
            )

        # Aynı dönemde aynı kişiye aynı tip feedback verilmiş mi?
        existing = db.query(Feedback).filter(
            Feedback.reviewer_id  == reviewer_employee_id,
            Feedback.reviewee_id  == feedback_data.reviewee_id,
            Feedback.feedback_type == feedback_data.feedback_type,
            Feedback.period_date  == feedback_data.period_date
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu kişiye bu dönem için zaten geri bildirim vermişsiniz"
            )

        # Eğer request_id verilmişse, o request gerçekten var mı ve sana mı ait?
        if feedback_data.request_id:
            req = db.query(FeedbackRequest).filter(
                FeedbackRequest.id        == feedback_data.request_id,
                FeedbackRequest.target_id == reviewer_employee_id
            ).first()
            if not req:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feedback talebi bulunamadı veya size ait değil"
                )

        # Feedback oluştur
        db_feedback = Feedback(
            reviewer_id           = reviewer_employee_id,
            reviewee_id           = feedback_data.reviewee_id,
            feedback_type         = feedback_data.feedback_type,
            period_date           = feedback_data.period_date,
            score_communication   = feedback_data.score_communication,
            score_teamwork        = feedback_data.score_teamwork,
            score_problem_solving = feedback_data.score_problem_solving,
            score_leadership      = feedback_data.score_leadership,
            score_technical       = feedback_data.score_technical,
            strength_text         = feedback_data.strength_text,
            improvement_text      = feedback_data.improvement_text,
            general_comment       = feedback_data.general_comment,
            is_anonymous          = feedback_data.is_anonymous,
            is_voice_input        = feedback_data.is_voice_input,
            request_id            = feedback_data.request_id,
        )
        db.add(db_feedback)

        # Eğer bir request'e bağlıysa, request'i tamamlandı olarak işaretle
        if feedback_data.request_id:
            req.status = FeedbackStatus.completed

        db.commit()
        db.refresh(db_feedback)
        return db_feedback

    # ──────────────────────────────────────────────
    # FEEDBACK — Listeleme
    # ──────────────────────────────────────────────

    @staticmethod
    def get_received_feedbacks(
        db: Session,
        employee_id: int,
        period_date: Optional[date] = None
    ) -> List[Feedback]:
        """Bir çalışanın aldığı tüm feedbackler"""
        query = db.query(Feedback).filter(
            Feedback.reviewee_id == employee_id
        )
        if period_date:
            query = query.filter(Feedback.period_date == period_date)
        return query.order_by(Feedback.created_at.desc()).all()

    @staticmethod
    def get_given_feedbacks(
        db: Session,
        employee_id: int
    ) -> List[Feedback]:
        """Bir çalışanın verdiği tüm feedbackler"""
        return db.query(Feedback).filter(
            Feedback.reviewer_id == employee_id
        ).order_by(Feedback.created_at.desc()).all()

    @staticmethod
    def get_department_feedbacks(
        db: Session,
        department_id: int,
        period_date: Optional[date] = None
    ) -> List[Feedback]:
        """Bir departmandaki tüm feedbackler (manager için)"""
        query = db.query(Feedback).join(
            Employee, Feedback.reviewee_id == Employee.id
        ).filter(
            Employee.department_id == department_id
        )
        if period_date:
            query = query.filter(Feedback.period_date == period_date)
        return query.order_by(Feedback.created_at.desc()).all()

    @staticmethod
    def get_all_feedbacks(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Feedback]:
        """Tüm feedbackler (sadece admin)"""
        return db.query(Feedback).offset(skip).limit(limit).all()

    # ──────────────────────────────────────────────
    # FEEDBACK — Özet / Dashboard
    # ──────────────────────────────────────────────

    @staticmethod
    def get_feedback_summary(
        db: Session,
        employee_id: int,
        period_date: Optional[date] = None
    ) -> FeedbackSummary:
        """Bir çalışanın feedback ortalamaları"""

        query = db.query(Feedback).filter(
            Feedback.reviewee_id == employee_id
        )
        if period_date:
            query = query.filter(Feedback.period_date == period_date)

        feedbacks = query.all()
        total = len(feedbacks)

        def avg(values):
            vals = [v for v in values if v is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        avg_comm    = avg([f.score_communication   for f in feedbacks])
        avg_team    = avg([f.score_teamwork         for f in feedbacks])
        avg_problem = avg([f.score_problem_solving  for f in feedbacks])
        avg_lead    = avg([f.score_leadership       for f in feedbacks])
        avg_tech    = avg([f.score_technical        for f in feedbacks])

        # Genel ortalama — mevcut skorların ortalaması
        all_avgs = [a for a in [avg_comm, avg_team, avg_problem, avg_lead, avg_tech] if a]
        overall  = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else None

        # Rozetler
        badges = db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee_id
        ).all()

        return FeedbackSummary(
            employee_id         = employee_id,
            total_received      = total,
            avg_communication   = avg_comm,
            avg_teamwork        = avg_team,
            avg_problem_solving = avg_problem,
            avg_leadership      = avg_lead,
            avg_technical       = avg_tech,
            overall_avg         = overall,
            badges              = [BadgeResponse.model_validate(b) for b in badges]
        )

    # ──────────────────────────────────────────────
    # FEEDBACK REQUEST — Talep Sistemi
    # ──────────────────────────────────────────────

    @staticmethod
    def create_feedback_request(
        db: Session,
        request_data: FeedbackRequestCreate,
        requester_employee_id: int
    ) -> FeedbackRequest:
        """Birinden feedback talep et"""

        # Kendinden talep etmeyi engelle
        if request_data.target_id == requester_employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kendinizden feedback talep edemezsiniz"
            )

        # Hedef çalışan var mı?
        target = db.query(Employee).filter(
            Employee.id == request_data.target_id
        ).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {request_data.target_id})"
            )

        # Aynı dönemde aynı kişiye zaten talep gönderilmiş mi?
        existing = db.query(FeedbackRequest).filter(
            FeedbackRequest.requester_id == requester_employee_id,
            FeedbackRequest.target_id    == request_data.target_id,
            FeedbackRequest.period_date  == request_data.period_date,
            FeedbackRequest.status       == FeedbackStatus.pending
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu kişiye bu dönem için zaten bekleyen bir talebiniz var"
            )

        db_request = FeedbackRequest(
            requester_id = requester_employee_id,
            target_id    = request_data.target_id,
            period_date  = request_data.period_date,
            deadline     = request_data.deadline,
            message      = request_data.message,
            status       = FeedbackStatus.pending
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def get_my_requests(
        db: Session,
        employee_id: int
    ) -> List[FeedbackRequest]:
        """Benden istenen feedback talepleri (henüz cevaplamadıklarım)"""
        return db.query(FeedbackRequest).filter(
            FeedbackRequest.target_id == employee_id,
            FeedbackRequest.status    == FeedbackStatus.pending
        ).order_by(FeedbackRequest.created_at.desc()).all()

    @staticmethod
    def update_request_status(
        db: Session,
        request_id: int,
        update_data: FeedbackRequestUpdate,
        employee_id: int
    ) -> FeedbackRequest:
        """Feedback talebini kabul et veya reddet"""
        req = db.query(FeedbackRequest).filter(
            FeedbackRequest.id        == request_id,
            FeedbackRequest.target_id == employee_id
        ).first()

        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talep bulunamadı veya size ait değil"
            )

        if req.status != FeedbackStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu talep zaten '{req.status.value}' durumunda"
            )

        req.status = update_data.status
        db.commit()
        db.refresh(req)
        return req

    # ──────────────────────────────────────────────
    # BADGE — Rozetler
    # ──────────────────────────────────────────────

    @staticmethod
    def get_employee_badges(
        db: Session,
        employee_id: int
    ) -> List[EmployeeBadge]:
        """Bir çalışanın tüm rozetleri"""
        return db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee_id
        ).order_by(EmployeeBadge.created_at.desc()).all()