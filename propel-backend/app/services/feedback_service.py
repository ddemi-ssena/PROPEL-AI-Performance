# propel-backend/app/services/feedback_service.py
# 360° Geri Bildirim Modülü — İş Mantığı

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta
from math import ceil
import random

from app.db.models.feedback import (
    Feedback, FeedbackRequest, EmployeeBadge,
    FeedbackType, FeedbackStatus, FeedbackQuestion, FeedbackResponse, FeedbackDirection,
    FeedbackAssignment, FeedbackAssignmentType, FeedbackAssignmentStatus
)
from app.db.models.employee import Employee
from app.db.models.user import User, UserRole
from app.db.models.department import Department
from app.schemas.feedback import (
    FeedbackCreate, FeedbackRequestCreate,
    FeedbackRequestUpdate, FeedbackSummary, BadgeResponse
)
from app.services.ai_service import AIService
from app.services.nlp_service import NLPService
from app.services.rag_service import RAGService
from app.db.models.nlp import NLPPeriodType


class FeedbackService:
    WEEKLY_THEME_BY_WEEK = {
        1: "Süreçler & Blokajlar",
        2: "Motivasyon & Psikolojik Durum",
        3: "İş Birliği & Şeffaflık",
        4: "Gelişim & Vizyon",
    }
    LOW_QUALITY_PHRASES = {
        "cok iyi",
        "çok iyi",
        "iyi",
        "guzel",
        "güzel",
        "super",
        "süper",
        "harika",
        "aynen devam",
        "boyle devam",
        "böyle devam",
        "gayet iyi",
        "eline saglik",
        "eline sağlık",
        "tebrikler",
    }

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

    @staticmethod
    def get_feedback_candidates(
        db: Session,
        current_employee_id: int
    ) -> List[Employee]:
        """
        Feedback verilebilecek genel adayları getirir.
        Not: Haftalık slot ve zorunlu atama kısıtları ayrı assignment endpoint'i ile yönetilir.
        """
        current_employee = db.query(Employee).join(Employee.user).filter(
            Employee.id == current_employee_id
        ).first()
        if not current_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Çalışan kaydınız bulunamadı"
            )

        query = db.query(Employee).join(Employee.user).filter(
            Employee.id != current_employee_id
        )

        if current_employee.user.role == UserRole.admin:
            return query.order_by(User.role.desc(), User.full_name.asc()).all()

        allowed_roles = [UserRole.employee, UserRole.department_manager]

        return query.filter(
            Employee.department_id == current_employee.department_id,
            User.role.in_(allowed_roles)
        ).order_by(User.role.desc(), User.full_name.asc()).all()

    @staticmethod
    def _get_current_period(target_date: Optional[date] = None) -> tuple[int, int, int]:
        dt = target_date or datetime.utcnow().date()
        return FeedbackService.get_week_of_month(dt), dt.month, dt.year

    @staticmethod
    def _get_previous_week_bounds(target_date: Optional[date] = None) -> tuple[datetime, datetime]:
        current_start, _ = FeedbackService.get_week_bounds(target_date)
        previous_start = current_start - timedelta(days=7)
        return previous_start, current_start

    @staticmethod
    def _is_consecutive_week_blocked(
        db: Session,
        *,
        sender_employee_id: int,
        target_employee_id: int,
        target_date: Optional[date] = None,
    ) -> bool:
        previous_start, previous_end = FeedbackService._get_previous_week_bounds(target_date)
        return db.query(FeedbackResponse).filter(
            FeedbackResponse.sender_id == sender_employee_id,
            FeedbackResponse.receiver_id == target_employee_id,
            FeedbackResponse.created_at >= previous_start,
            FeedbackResponse.created_at < previous_end,
        ).count() > 0

    @staticmethod
    def _is_saturated_pair(
        db: Session,
        *,
        sender_employee_id: int,
        target_employee_id: int,
        target_date: Optional[date] = None,
    ) -> bool:
        current_start, _ = FeedbackService.get_week_bounds(target_date)
        rolling_start = current_start - timedelta(days=28)
        count = db.query(FeedbackResponse).filter(
            FeedbackResponse.sender_id == sender_employee_id,
            FeedbackResponse.receiver_id == target_employee_id,
            FeedbackResponse.created_at >= rolling_start,
            FeedbackResponse.created_at < current_start,
        ).count()
        return count >= 3

    @staticmethod
    def _already_feedbacked_this_week(
        db: Session,
        *,
        sender_employee_id: int,
        target_employee_id: int,
        target_date: Optional[date] = None,
    ) -> bool:
        week_start, week_end = FeedbackService.get_week_bounds(target_date)
        return db.query(FeedbackResponse).filter(
            FeedbackResponse.sender_id == sender_employee_id,
            FeedbackResponse.receiver_id == target_employee_id,
            FeedbackResponse.created_at >= week_start,
            FeedbackResponse.created_at < week_end,
        ).count() > 0

    @staticmethod
    def _is_candidate_blocked(
        db: Session,
        *,
        sender_employee_id: int,
        target_employee_id: int,
        target_date: Optional[date] = None,
    ) -> bool:
        return (
            FeedbackService._is_consecutive_week_blocked(
                db,
                sender_employee_id=sender_employee_id,
                target_employee_id=target_employee_id,
                target_date=target_date,
            )
            or FeedbackService._is_saturated_pair(
                db,
                sender_employee_id=sender_employee_id,
                target_employee_id=target_employee_id,
                target_date=target_date,
            )
            or FeedbackService._already_feedbacked_this_week(
                db,
                sender_employee_id=sender_employee_id,
                target_employee_id=target_employee_id,
                target_date=target_date,
            )
        )

    @staticmethod
    def _weekly_completion_count(
        db: Session,
        *,
        sender_employee_id: int,
        target_date: Optional[date] = None,
    ) -> int:
        return FeedbackService.count_weekly_feedbacks(db, sender_employee_id, target_date)

    @staticmethod
    def _normalize_text_for_checks(value: str) -> str:
        return " ".join((value or "").strip().lower().split())

    @staticmethod
    def _detect_low_quality_feedback(response_text: str) -> dict:
        normalized = FeedbackService._normalize_text_for_checks(response_text)
        tokens = [token for token in normalized.split(" ") if token]
        token_count = len(tokens)
        char_count = len(normalized)
        unique_ratio = (len(set(tokens)) / token_count) if token_count else 0.0

        reasons: list[str] = []
        score = 0.0

        if char_count < 20:
            reasons.append("cok_kisa_yanit")
            score += 0.45
        elif char_count < 35:
            reasons.append("kisa_yanit")
            score += 0.25

        if token_count < 4:
            reasons.append("dusuk_kelime_sayisi")
            score += 0.3
        elif token_count < 7:
            reasons.append("sinirli_kelime_cesitliligi")
            score += 0.15

        if unique_ratio and unique_ratio < 0.55:
            reasons.append("tekrarlayan_ifadeler")
            score += 0.2

        if normalized in FeedbackService.LOW_QUALITY_PHRASES:
            reasons.append("genel_gecer_ifade")
            score += 0.5

        if any(phrase in normalized for phrase in FeedbackService.LOW_QUALITY_PHRASES if len(phrase) > 5):
            reasons.append("kalip_yanit")
            score += 0.2

        is_low_quality = score >= 0.45
        return {
            "is_low_quality": is_low_quality,
            "quality_score": round(max(0.0, min(score, 1.0)), 2),
            "quality_reasons": sorted(set(reasons)),
        }

    @staticmethod
    def _detect_reciprocity_bias(
        db: Session,
        *,
        feedback_response: FeedbackResponse,
    ) -> dict:
        week_start, week_end = FeedbackService.get_week_bounds(feedback_response.created_at.date())
        reverse_row = db.query(FeedbackResponse).filter(
            FeedbackResponse.sender_id == feedback_response.receiver_id,
            FeedbackResponse.receiver_id == feedback_response.sender_id,
            FeedbackResponse.created_at >= week_start,
            FeedbackResponse.created_at < week_end,
            FeedbackResponse.id != feedback_response.id,
        ).order_by(FeedbackResponse.created_at.desc()).first()

        if not reverse_row:
            return {
                "reciprocity_bias_suspected": False,
                "reciprocity_bias_score": 0.0,
                "reciprocity_bias_reasons": [],
            }

        current_scores = [
            feedback_response.score_communication,
            feedback_response.score_teamwork,
            feedback_response.score_leadership,
            feedback_response.score_technical,
        ]
        reverse_scores = [
            reverse_row.score_communication,
            reverse_row.score_teamwork,
            reverse_row.score_leadership,
            reverse_row.score_technical,
        ]
        current_avg = sum(current_scores) / len(current_scores)
        reverse_avg = sum(reverse_scores) / len(reverse_scores)
        average_gap = abs(current_avg - reverse_avg)

        reasons: list[str] = ["ayni_hafta_karsilikli_geri_bildirim"]
        score = 0.35

        if current_avg >= 4.5 and reverse_avg >= 4.5:
            reasons.append("karsilikli_yuksek_puan")
            score += 0.35
        elif current_avg <= 2.0 and reverse_avg <= 2.0:
            reasons.append("karsilikli_dusuk_puan")
            score += 0.35

        if average_gap <= 0.35:
            reasons.append("puanlar_birbirine_cok_yakin")
            score += 0.15

        current_quality = FeedbackService._detect_low_quality_feedback(feedback_response.response_text)
        reverse_quality = FeedbackService._detect_low_quality_feedback(reverse_row.response_text)
        if current_quality["is_low_quality"] and reverse_quality["is_low_quality"]:
            reasons.append("iki_yonlu_dusuk_kalite_yanit")
            score += 0.2

        return {
            "reciprocity_bias_suspected": score >= 0.55,
            "reciprocity_bias_score": round(max(0.0, min(score, 1.0)), 2),
            "reciprocity_bias_reasons": reasons,
            "paired_feedback_response_id": reverse_row.id,
        }

    @staticmethod
    def _current_slot_for_sender(
        db: Session,
        *,
        sender_employee_id: int,
        target_date: Optional[date] = None,
    ) -> str:
        completed_count = FeedbackService._weekly_completion_count(
            db,
            sender_employee_id=sender_employee_id,
            target_date=target_date,
        )
        if completed_count <= 0:
            return "mandatory_random"
        if completed_count == 1:
            return "department_internal"
        if completed_count == 2:
            return "cross_functional"
        return "completed"

    @staticmethod
    def _least_feedback_targets_in_department(
        db: Session,
        *,
        sender_employee: Employee,
        target_date: Optional[date] = None,
    ) -> List[Employee]:
        candidates = db.query(Employee).join(Employee.user).filter(
            Employee.department_id == sender_employee.department_id,
            Employee.id != sender_employee.id,
        ).all()

        valid_candidates = []
        for candidate in candidates:
            if FeedbackService._is_candidate_blocked(
                db,
                sender_employee_id=sender_employee.id,
                target_employee_id=candidate.id,
                target_date=target_date,
            ):
                continue
            valid_candidates.append(candidate)

        if not valid_candidates:
            return []

        dt = target_date or datetime.utcnow().date()
        counts: dict[int, int] = {}
        for candidate in valid_candidates:
            counts[candidate.id] = db.query(FeedbackResponse).filter(
                FeedbackResponse.receiver_id == candidate.id,
                FeedbackResponse.period_month == dt.month,
                FeedbackResponse.period_year == dt.year,
            ).count()

        min_count = min(counts.values())
        return [candidate for candidate in valid_candidates if counts[candidate.id] == min_count]

    @staticmethod
    def ensure_weekly_mandatory_assignment(
        db: Session,
        *,
        current_employee: Employee,
        target_date: Optional[date] = None,
    ) -> Optional[FeedbackAssignment]:
        week_number, month_number, year_number = FeedbackService._get_current_period(target_date)

        assignment = db.query(FeedbackAssignment).filter(
            FeedbackAssignment.sender_id == current_employee.id,
            FeedbackAssignment.assignment_type == FeedbackAssignmentType.mandatory_random,
            FeedbackAssignment.period_week == week_number,
            FeedbackAssignment.period_month == month_number,
            FeedbackAssignment.period_year == year_number,
        ).first()
        if assignment:
            return assignment

        target_pool = FeedbackService._least_feedback_targets_in_department(
            db,
            sender_employee=current_employee,
            target_date=target_date,
        )
        if not target_pool:
            return None

        target = random.SystemRandom().choice(target_pool)
        assignment = FeedbackAssignment(
            sender_id=current_employee.id,
            target_id=target.id,
            assignment_type=FeedbackAssignmentType.mandatory_random,
            status=FeedbackAssignmentStatus.pending,
            period_week=week_number,
            period_month=month_number,
            period_year=year_number,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def _base_candidate_query(
        db: Session,
        *,
        current_employee: Employee,
    ) -> List[Employee]:
        return db.query(Employee).join(Employee.user).filter(
            Employee.id != current_employee.id
        ).order_by(User.role.desc(), User.full_name.asc()).all()

    @staticmethod
    def get_weekly_assignment_state(
        db: Session,
        *,
        current_employee_id: int,
        target_date: Optional[date] = None,
    ) -> dict:
        current_employee = db.query(Employee).join(Employee.user).filter(
            Employee.id == current_employee_id
        ).first()
        if not current_employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Çalışan kaydınız bulunamadı")

        completed_count = FeedbackService._weekly_completion_count(
            db,
            sender_employee_id=current_employee.id,
            target_date=target_date,
        )
        required_count = 3
        remaining_count = max(required_count - completed_count, 0)
        current_slot = FeedbackService._current_slot_for_sender(
            db,
            sender_employee_id=current_employee.id,
            target_date=target_date,
        )

        mandatory_assignment = FeedbackService.ensure_weekly_mandatory_assignment(
            db,
            current_employee=current_employee,
            target_date=target_date,
        )

        all_candidates = FeedbackService._base_candidate_query(db, current_employee=current_employee)
        department_candidates: List[Employee] = []
        cross_functional_candidates: List[Employee] = []

        for candidate in all_candidates:
            if FeedbackService._is_candidate_blocked(
                db,
                sender_employee_id=current_employee.id,
                target_employee_id=candidate.id,
                target_date=target_date,
            ):
                continue

            if candidate.department_id == current_employee.department_id:
                department_candidates.append(candidate)
            else:
                cross_functional_candidates.append(candidate)

        available_candidates: List[Employee]
        assignment_required = False
        if current_slot == "mandatory_random" and mandatory_assignment and mandatory_assignment.status == FeedbackAssignmentStatus.pending:
            available_candidates = [mandatory_assignment.target] if mandatory_assignment.target else []
            assignment_required = True
        elif current_slot == "department_internal":
            available_candidates = [candidate for candidate in department_candidates if not mandatory_assignment or candidate.id != mandatory_assignment.target_id]
        elif current_slot == "cross_functional":
            available_candidates = department_candidates
        else:
            available_candidates = department_candidates

        rules_summary = [
            "İlk slot sistemin atadığı zorunlu kişiye ayrılır.",
            "İkinci slot kendi departmanından bir kişiye verilmelidir.",
            "Üçüncü slot da yalnızca kendi departmanınız içinden seçilir.",
            "Aynı kişiye iki hafta üst üste geri bildirim verilemez.",
            "Son 4 haftada aynı kişiye 3 kez geri bildirim verdiyseniz bu hafta listede görünmez.",
        ]

        week_number, _, _ = FeedbackService._get_current_period(target_date)
        return {
            "week_number": week_number,
            "required_count": required_count,
            "completed_count": completed_count,
            "remaining_count": remaining_count,
            "is_completed": completed_count >= required_count,
            "current_slot": current_slot,
            "assignment_required": assignment_required,
            "mandatory_assignment": mandatory_assignment,
            "available_candidates": available_candidates,
            "department_candidates": department_candidates,
            "cross_functional_candidates": cross_functional_candidates,
            "rules_summary": rules_summary,
        }

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
        today = datetime.utcnow().date()
        current_period = today.replace(day=1)
        badges = db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee_id,
            EmployeeBadge.period_date == current_period,
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
        """Bir çalışanın aktif aylık rozetleri"""
        today = datetime.utcnow().date()
        current_period = today.replace(day=1)
        return db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee_id,
            EmployeeBadge.period_date == current_period,
        ).order_by(EmployeeBadge.created_at.desc()).all()

    @staticmethod
    def get_week_of_month(target_date: Optional[date] = None) -> int:
        dt = target_date or datetime.utcnow().date()
        first_day = dt.replace(day=1)
        adjusted_dom = dt.day + first_day.weekday()
        week_of_month = ceil(adjusted_dom / 7)
        return min(max(week_of_month, 1), 4)

    @staticmethod
    def _resolve_direction(sender_role: UserRole, receiver_role: UserRole) -> FeedbackDirection:
        if sender_role == UserRole.department_manager and receiver_role == UserRole.employee:
            return FeedbackDirection.manager_to_employee
        if sender_role == UserRole.employee and receiver_role == UserRole.department_manager:
            return FeedbackDirection.employee_to_manager
        if sender_role == UserRole.department_manager and receiver_role == UserRole.department_manager:
            return FeedbackDirection.manager_to_manager
        if sender_role == UserRole.employee and receiver_role == UserRole.employee:
            return FeedbackDirection.employee_to_employee
        return FeedbackDirection.peer_to_peer

    @staticmethod
    def _normalize_direction_for_question(direction: FeedbackDirection) -> FeedbackDirection:
        """
        Soru havuzu / seed tarafinda genelde 'peer_to_peer' sorulari var.
        'employee_to_employee' ve 'manager_to_manager' gibi varyantlari soru bazinda
        peer_to_peer'a indirgeriz ki hem seed hem AI prompt daha dogal olsun.
        """
        if direction in (FeedbackDirection.employee_to_employee, FeedbackDirection.manager_to_manager):
            return FeedbackDirection.peer_to_peer
        return direction

    @staticmethod
    def _direction_label_tr(direction: FeedbackDirection) -> str:
        labels = {
            FeedbackDirection.manager_to_employee: "Yöneticiden Çalışana",
            FeedbackDirection.employee_to_manager: "Çalışandan Yöneticiye",
            FeedbackDirection.peer_to_peer: "Eş Değerlendirme",
            FeedbackDirection.manager_to_manager: "Yönetici - Yönetici",
            FeedbackDirection.employee_to_employee: "Çalışan - Çalışan",
        }
        return labels.get(direction, "Eş Değerlendirme")

    @staticmethod
    def get_current_weekly_question(
        db: Session,
        sender_employee_id: int,
        receiver_employee_id: int
    ) -> FeedbackQuestion:
        sender = db.query(Employee).join(Employee.user).filter(Employee.id == sender_employee_id).first()
        receiver = db.query(Employee).join(Employee.user).filter(Employee.id == receiver_employee_id).first()

        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Gönderen veya alıcı çalışan bulunamadı")
        if sender.id == receiver.id:
            raise HTTPException(status_code=400, detail="Kendinize geri bildirim veremezsiniz")

        week_number = FeedbackService.get_week_of_month()
        raw_direction = FeedbackService._resolve_direction(sender.user.role, receiver.user.role)
        fallback_direction = FeedbackService._normalize_direction_for_question(raw_direction)
        category = FeedbackService.WEEKLY_THEME_BY_WEEK[week_number]
        target_department_id = receiver.department_id

        # 1) Once tam baglama gore AI-generated cache varsa onu kullan
        question = db.query(FeedbackQuestion).filter(
            FeedbackQuestion.week_number == week_number,
            FeedbackQuestion.direction == raw_direction,
            FeedbackQuestion.department_id == target_department_id,
            FeedbackQuestion.is_ai_generated.is_(True),
        ).order_by(FeedbackQuestion.id.desc()).first()

        if question:
            return question

        # 1b) Peer varyantlari icin normalize edilmis eski cache de varsa onu kullan
        if fallback_direction != raw_direction:
            question = db.query(FeedbackQuestion).filter(
                FeedbackQuestion.week_number == week_number,
                FeedbackQuestion.direction == fallback_direction,
                FeedbackQuestion.department_id == target_department_id,
                FeedbackQuestion.is_ai_generated.is_(True),
            ).order_by(FeedbackQuestion.id.desc()).first()
            if question:
                return question

        # 2) AI ile uretmeyi dene (degerlendirilen kisinin departmani ve rolune gore)
        dept_name = "Genel"
        if target_department_id:
            dept = db.query(Department).filter(Department.id == target_department_id).first()
            if dept:
                dept_name = dept.name

        ai_question = AIService.generate_weekly_question(
            dept_name,
            receiver.user.role,
            category,
            FeedbackService._direction_label_tr(raw_direction),
        )
        if ai_question:
            question = FeedbackQuestion(
                week_number=week_number,
                direction=raw_direction,
                category=category,
                department_id=target_department_id,
                question_text=ai_question,
                is_ai_generated=True,
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            return question

        # 3) AI basarisizsa haftaya ve role gore deterministic akilli fallback uret
        template_question = AIService.build_template_question(
            dept_name,
            receiver.user.role,
            category,
        )
        existing_template = db.query(FeedbackQuestion).filter(
            FeedbackQuestion.week_number == week_number,
            FeedbackQuestion.direction == raw_direction,
            FeedbackQuestion.department_id == target_department_id,
            FeedbackQuestion.question_text == template_question,
        ).order_by(FeedbackQuestion.id.desc()).first()
        if existing_template:
            return existing_template

        question = FeedbackQuestion(
            week_number=week_number,
            direction=raw_direction,
            category=category,
            department_id=target_department_id,
            question_text=template_question,
            is_ai_generated=False,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

        # 4) Son care: once tam yonlu seed/genel havuzdan getir
        fallback = db.query(FeedbackQuestion).filter(
            FeedbackQuestion.week_number == week_number,
            FeedbackQuestion.direction == raw_direction,
            or_(
                FeedbackQuestion.department_id == target_department_id,
                FeedbackQuestion.department_id.is_(None),
            ),
        ).order_by(
            FeedbackQuestion.department_id.is_(None).asc(),
            FeedbackQuestion.id.asc(),
        ).first()
        if fallback:
            return fallback

        # 3b) Tam yonlu soru yoksa normalize edilmis yonde ara
        if fallback_direction != raw_direction:
            fallback = db.query(FeedbackQuestion).filter(
                FeedbackQuestion.week_number == week_number,
                FeedbackQuestion.direction == fallback_direction,
                or_(
                    FeedbackQuestion.department_id == target_department_id,
                    FeedbackQuestion.department_id.is_(None),
                ),
            ).order_by(
                FeedbackQuestion.department_id.is_(None).asc(),
                FeedbackQuestion.id.asc(),
            ).first()
            if fallback:
                return fallback

        # 5) Hic soru yoksa basit fallback soru olustur
        question = FeedbackQuestion(
            week_number=week_number,
            direction=raw_direction,
            category=category,
            department_id=target_department_id,
            question_text=f"Bu hafta {category} temasinda bu kisinin en kritik davranis veya destek ihtiyaci neydi?",
            is_ai_generated=False,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def get_week_bounds(target_date: Optional[date] = None) -> tuple[datetime, datetime]:
        dt = target_date or datetime.utcnow().date()
        start_date = dt - timedelta(days=dt.weekday())
        end_date = start_date + timedelta(days=7)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())
        return start_dt, end_dt

    @staticmethod
    def count_weekly_feedbacks(db: Session, sender_employee_id: int, target_date: Optional[date] = None) -> int:
        week_start, week_end = FeedbackService.get_week_bounds(target_date)
        return db.query(FeedbackResponse).filter(
            FeedbackResponse.sender_id == sender_employee_id,
            FeedbackResponse.created_at >= week_start,
            FeedbackResponse.created_at < week_end
        ).count()

    @staticmethod
    def submit_weekly_feedback(
        db: Session,
        sender_employee_id: int,
        receiver_employee_id: int,
        response_text: str,
        score_communication: float,
        score_teamwork: float,
        score_leadership: float,
        score_technical: float,
    ) -> FeedbackResponse:
        if not response_text.strip():
            raise HTTPException(status_code=400, detail="Metin alanlari bos birakilamaz")

        sender = db.query(Employee).join(Employee.user).filter(Employee.id == sender_employee_id).first()
        receiver = db.query(Employee).join(Employee.user).filter(Employee.id == receiver_employee_id).first()
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Gonderen veya alici calisan bulunamadi")

        state = FeedbackService.get_weekly_assignment_state(
            db,
            current_employee_id=sender_employee_id,
        )
        current_slot = state["current_slot"]
        mandatory_assignment: FeedbackAssignment | None = state["mandatory_assignment"]

        if current_slot == "mandatory_random" and mandatory_assignment and mandatory_assignment.status == FeedbackAssignmentStatus.pending:
            if receiver_employee_id != mandatory_assignment.target_id:
                raise HTTPException(
                    status_code=400,
                    detail="Bu hafta once sistemin atadigi zorunlu kisiyi tamamlamalisiniz.",
                )

        if current_slot in {"department_internal", "cross_functional"} and receiver.department_id != sender.department_id:
            raise HTTPException(
                status_code=400,
                detail="Bu asamadaki feedback hakki sadece kendi departmaniniz icindeki bir kisiye verilebilir.",
            )

        if FeedbackService._is_candidate_blocked(
            db,
            sender_employee_id=sender_employee_id,
            target_employee_id=receiver_employee_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Bu kisi bu hafta secilemez. Sistem ardışık hafta veya doygunluk kurali nedeniyle engelledi.",
            )

        question = FeedbackService.get_current_weekly_question(db, sender_employee_id, receiver_employee_id)

        row = FeedbackResponse(
            sender_id=sender_employee_id,
            receiver_id=receiver_employee_id,
            question_id=question.id,
            response_text=response_text.strip(),
            score_communication=int(score_communication),
            score_teamwork=int(score_teamwork),
            score_leadership=int(score_leadership),
            score_technical=int(score_technical),
            period_week=FeedbackService.get_week_of_month(),
            period_month=datetime.utcnow().month,
            period_year=datetime.utcnow().year,
            nlp_analysis=None
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        if receiver:
            quality_payload = FeedbackService._detect_low_quality_feedback(row.response_text)
            reciprocity_payload = FeedbackService._detect_reciprocity_bias(
                db,
                feedback_response=row,
            )
            dept_name = receiver.department.name if receiver.department else "Genel"
            analysis_payload, model_provider, model_name = AIService.analyze_weekly_feedback(
                dept_name=dept_name,
                target_role=receiver.user.role,
                week_theme=question.category,
                direction_label_tr=FeedbackService._direction_label_tr(question.direction),
                question_text=question.question_text,
                response_text=row.response_text,
                score_communication=float(row.score_communication),
                score_teamwork=float(row.score_teamwork),
                score_leadership=float(row.score_leadership),
                score_technical=float(row.score_technical),
            )

            quality_flags: list[str] = []
            if quality_payload["is_low_quality"]:
                quality_flags.append("dusuk_veri_kalitesi")
            if reciprocity_payload["reciprocity_bias_suspected"]:
                quality_flags.append("karsilikli_puan_bias_suphesi")

            existing_risk_flags = [
                str(item).strip()
                for item in (analysis_payload.get("risk_flags") or [])
                if str(item).strip()
            ]
            analysis_payload["risk_flags"] = list(dict.fromkeys(existing_risk_flags + quality_flags))
            analysis_payload["quality_signal"] = quality_payload
            analysis_payload["reciprocity_signal"] = reciprocity_payload

            NLPService.save_weekly_analysis(
                db,
                feedback_response=row,
                analysis_payload=analysis_payload,
                analysis_version="v1",
                model_provider=model_provider,
                model_name=model_name,
            )
            NLPService.rebuild_employee_profile(
                db,
                employee_id=receiver.id,
                period_type=NLPPeriodType.weekly,
                period_year=row.period_year,
                period_month=row.period_month,
                period_week=row.period_week,
            )
            NLPService.refresh_employee_monthly_badges(
                db,
                employee_id=receiver.id,
                period_year=row.period_year,
                period_month=row.period_month,
            )
            RAGService.upsert_weekly_feedback_memory(
                db,
                feedback_response=row,
                analysis_payload=analysis_payload,
            )
            if mandatory_assignment and mandatory_assignment.status == FeedbackAssignmentStatus.pending and mandatory_assignment.target_id == receiver.id:
                mandatory_assignment.status = FeedbackAssignmentStatus.completed
                mandatory_assignment.completed_feedback_response_id = row.id
            db.commit()
            db.refresh(row)
        return row
