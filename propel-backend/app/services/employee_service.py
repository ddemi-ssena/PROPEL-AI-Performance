from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload, Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.nlp import EmployeeNLPProfile, NLPPeriodType
from app.db.models.survey_response import SurveyResponse
from app.db.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    TeamHealthMember,
    TeamHealthResponse,
    TeamHealthSourceSummary,
    TeamHealthStat,
)
from app.services.analytics_service import AnalyticsService


class EmployeeService:
    RISK_LEVEL_SCORE = {
        "low": 20.0,
        "medium": 60.0,
        "high": 90.0,
    }

    @staticmethod
    def _validate_external_employee_code(
        db: Session,
        external_employee_code: str | None,
        current_employee_id: int | None = None,
    ) -> None:
        if not external_employee_code:
            return

        existing = (
            db.query(Employee)
            .filter(Employee.external_employee_code == external_employee_code)
            .first()
        )
        if existing and existing.id != current_employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu external_employee_code zaten kullaniliyor: {external_employee_code}"
                ),
            )

    @staticmethod
    def create_employee(db: Session, emp_data: EmployeeCreate) -> Employee:
        """Yeni calisan olustur."""
        user = db.query(User).filter(User.id == emp_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kullanici bulunamadi (ID: {emp_data.user_id})",
            )

        existing_employee = db.query(Employee).filter(Employee.user_id == emp_data.user_id).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Bu kullanici zaten bir calisan olarak kayitli "
                    f"(Employee ID: {existing_employee.id})"
                ),
            )

        department = db.query(Department).filter(Department.id == emp_data.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadi (ID: {emp_data.department_id})",
            )

        EmployeeService._validate_external_employee_code(
            db,
            emp_data.external_employee_code,
        )

        db_employee = Employee(**emp_data.dict())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def _attach_latest_surveys(employees: List[Employee]) -> List[Employee]:
        for emp in employees:
            if getattr(emp, "survey_responses", None):
                latest = sorted(emp.survey_responses, key=lambda x: x.period_date, reverse=True)[0]
                setattr(emp, "latest_ms", latest.score)
                setattr(emp, "latest_mte", getattr(latest, "mte_score", None))
                setattr(emp, "latest_ars", getattr(latest, "ars_score", None))

                ars = getattr(latest, "ars_score", None)
                if ars is not None:
                    if ars >= 0.6:
                        setattr(emp, "risk_level", "High")
                    elif ars >= 0.2:
                        setattr(emp, "risk_level", "Medium")
                    else:
                        setattr(emp, "risk_level", "Low")
                else:
                    setattr(emp, "risk_level", "Low")
            else:
                setattr(emp, "latest_ms", None)
                setattr(emp, "latest_mte", None)
                setattr(emp, "latest_ars", None)
                setattr(emp, "risk_level", "Low")
        return employees

    @staticmethod
    def get_all_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
        employees = db.query(Employee).offset(skip).limit(limit).all()
        return EmployeeService._attach_latest_surveys(employees)

    @staticmethod
    def get_employee_by_id(db: Session, emp_id: int) -> Employee:
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calisan bulunamadi (ID: {emp_id})",
            )
        return EmployeeService._attach_latest_surveys([employee])[0]

    @staticmethod
    def get_employees_by_department(db: Session, dept_id: int) -> List[Employee]:
        department = db.query(Department).filter(Department.id == dept_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadi (ID: {dept_id})",
            )

        employees = db.query(Employee).filter(Employee.department_id == dept_id).all()
        return EmployeeService._attach_latest_surveys(employees)

    @staticmethod
    def get_team_health(db: Session, current_user: User) -> TeamHealthResponse:
        scope_department_id: int | None = None
        if current_user.role != "admin":
            current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
            if not current_employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Calisan kaydiniz bulunamadi",
                )
            scope_department_id = current_employee.department_id

        query = db.query(Employee).options(
            joinedload(Employee.user),
            joinedload(Employee.department),
        )
        if scope_department_id:
            query = query.filter(Employee.department_id == scope_department_id)
        employees = query.all()
        employee_ids = [employee.id for employee in employees]

        performance = AnalyticsService.get_performance_summary(
            db=db,
            current_user=current_user,
            department_id=scope_department_id,
        )
        performance_by_employee = {row.employee_id: row for row in performance.employees}

        latest_surveys = EmployeeService._latest_surveys_by_employee(db, employee_ids)
        latest_profiles = EmployeeService._latest_profiles_by_employee(db, employee_ids)

        members: list[TeamHealthMember] = []
        for employee in employees:
            performance_row = performance_by_employee.get(employee.id)
            survey = latest_surveys.get(employee.id)
            profile = latest_profiles.get(employee.id)
            risk_score = EmployeeService._combined_risk_score(performance_row, survey, profile)
            risk_level = EmployeeService._risk_level_from_score(risk_score)
            data_sources = EmployeeService._data_sources(performance_row, survey, profile)
            members.append(
                TeamHealthMember(
                    id=employee.id,
                    name=employee.full_name,
                    role=employee.position or employee.user.role,
                    team=employee.team,
                    external_employee_code=employee.external_employee_code,
                    latest_pulse_score=round(float(survey.score), 2) if survey else None,
                    latest_mte=round(float(survey.mte_score), 3) if survey and survey.mte_score is not None else None,
                    latest_ars=round(float(survey.ars_score), 3) if survey and survey.ars_score is not None else None,
                    kpi_score=performance_row.kpi_score if performance_row else None,
                    kpi_trend=performance_row.trend if performance_row else None,
                    kpi_latest_period=performance_row.latest_period if performance_row else None,
                    feedback_count=profile.feedback_count if profile else 0,
                    feedback_sentiment_score=round(float(profile.avg_sentiment_score), 2) if profile and profile.avg_sentiment_score is not None else None,
                    feedback_motivation_score=round(float(profile.avg_motivation_score), 2) if profile and profile.avg_motivation_score is not None else None,
                    feedback_flight_risk_level=profile.flight_risk_level.value if profile and profile.flight_risk_level else None,
                    feedback_burnout_risk_level=profile.burnout_risk_level.value if profile and profile.burnout_risk_level else None,
                    combined_risk_score=risk_score,
                    combined_risk_level=risk_level,
                    recommended_action=EmployeeService._recommended_action(risk_level, performance_row, survey, profile),
                    data_sources=data_sources,
                )
            )

        members = sorted(
            members,
            key=lambda member: (member.combined_risk_score, member.name),
            reverse=True,
        )
        source_summary = TeamHealthSourceSummary(
            kpi_analyzed_count=len([member for member in members if member.kpi_score is not None]),
            pulse_response_count=len([member for member in members if member.latest_pulse_score is not None]),
            feedback_profile_count=len([member for member in members if member.feedback_count > 0]),
            latest_kpi_period=performance.latest_period,
            latest_pulse_period=max((survey.period_date for survey in latest_surveys.values()), default=None),
            latest_feedback_update=max((profile.updated_at for profile in latest_profiles.values()), default=None),
        )

        department = employees[0].department if employees else None
        return TeamHealthResponse(
            generated_at=datetime.now(timezone.utc),
            department_id=department.id if department else scope_department_id,
            department_name=department.name if department else None,
            member_count=len(members),
            stats=EmployeeService._team_health_stats(members, source_summary),
            source_summary=source_summary,
            members=members,
        )

    @staticmethod
    def _latest_surveys_by_employee(db: Session, employee_ids: list[int]) -> dict[int, SurveyResponse]:
        if not employee_ids:
            return {}
        surveys = (
            db.query(SurveyResponse)
            .filter(SurveyResponse.employee_id.in_(employee_ids))
            .filter(SurveyResponse.survey_type == "weekly_pulse")
            .order_by(SurveyResponse.period_date.desc(), SurveyResponse.created_at.desc())
            .all()
        )
        latest: dict[int, SurveyResponse] = {}
        for survey in surveys:
            latest.setdefault(survey.employee_id, survey)
        return latest

    @staticmethod
    def _latest_profiles_by_employee(db: Session, employee_ids: list[int]) -> dict[int, EmployeeNLPProfile]:
        if not employee_ids:
            return {}
        profiles = (
            db.query(EmployeeNLPProfile)
            .filter(EmployeeNLPProfile.employee_id.in_(employee_ids))
            .filter(EmployeeNLPProfile.period_type == NLPPeriodType.weekly)
            .order_by(
                EmployeeNLPProfile.period_year.desc(),
                EmployeeNLPProfile.period_month.desc(),
                EmployeeNLPProfile.period_week.desc(),
                EmployeeNLPProfile.updated_at.desc(),
            )
            .all()
        )
        latest: dict[int, EmployeeNLPProfile] = {}
        for profile in profiles:
            latest.setdefault(profile.employee_id, profile)
        return latest

    @staticmethod
    def _combined_risk_score(performance_row, survey: SurveyResponse | None, profile: EmployeeNLPProfile | None) -> float:
        signals: list[tuple[float, float]] = []
        if performance_row and performance_row.kpi_score is not None:
            kpi_risk = max(0.0, min(100.0, 100.0 - float(performance_row.kpi_score)))
            if performance_row.trend is not None and performance_row.trend < 0:
                kpi_risk = min(100.0, kpi_risk + min(20.0, abs(float(performance_row.trend)) * 2))
            signals.append((kpi_risk, 0.4))
        if survey and survey.ars_score is not None:
            signals.append((max(0.0, min(100.0, float(survey.ars_score) * 100.0)), 0.35))
        if profile:
            feedback_scores: list[float] = []
            if profile.flight_risk_level:
                feedback_scores.append(EmployeeService.RISK_LEVEL_SCORE.get(profile.flight_risk_level.value, 50.0))
            if profile.burnout_risk_level:
                feedback_scores.append(EmployeeService.RISK_LEVEL_SCORE.get(profile.burnout_risk_level.value, 50.0))
            if profile.avg_motivation_score is not None:
                feedback_scores.append(EmployeeService._inverse_score(profile.avg_motivation_score))
            if feedback_scores:
                signals.append((sum(feedback_scores) / len(feedback_scores), 0.25))
        if not signals:
            return 0.0
        total_weight = sum(weight for _, weight in signals)
        return round(sum(value * weight for value, weight in signals) / total_weight, 1)

    @staticmethod
    def _inverse_score(value: float) -> float:
        numeric = float(value)
        if numeric <= 1:
            normalized = numeric * 100.0
        elif numeric <= 5:
            normalized = numeric * 20.0
        else:
            normalized = numeric
        return max(0.0, min(100.0, 100.0 - normalized))

    @staticmethod
    def _risk_level_from_score(score: float) -> str:
        if score >= 67:
            return "High"
        if score >= 34:
            return "Medium"
        return "Low"

    @staticmethod
    def _data_sources(performance_row, survey: SurveyResponse | None, profile: EmployeeNLPProfile | None) -> list[str]:
        sources: list[str] = []
        if performance_row and performance_row.kpi_score is not None:
            sources.append("KPI")
        if survey:
            sources.append("Nabiz")
        if profile and profile.feedback_count > 0:
            sources.append("360")
        return sources

    @staticmethod
    def _recommended_action(
        risk_level: str,
        performance_row,
        survey: SurveyResponse | None,
        profile: EmployeeNLPProfile | None,
    ) -> str:
        if risk_level == "High":
            return "Risk toplantisi planla"
        if survey and survey.mte_score is not None and survey.mte_score < -0.1:
            return "Motivasyon dususunu gorus"
        if profile and (profile.flight_risk_level and profile.flight_risk_level.value in {"medium", "high"}):
            return "360 geri bildirim bulgularini konus"
        if performance_row and performance_row.trend is not None and performance_row.trend < 0:
            return "KPI trendini takip et"
        return "Duzenli takip"

    @staticmethod
    def _team_health_stats(members: list[TeamHealthMember], source_summary: TeamHealthSourceSummary) -> list[TeamHealthStat]:
        total = max(len(members), 1)
        pulse_scores = [member.latest_pulse_score for member in members if member.latest_pulse_score is not None]
        risky_count = len([member for member in members if member.combined_risk_level in {"High", "Medium"}])
        high_risk_count = len([member for member in members if member.combined_risk_level == "High"])
        avg_pulse = round(sum(pulse_scores) / len(pulse_scores), 1) if pulse_scores else None
        confidence = round(
            (
                (source_summary.kpi_analyzed_count / total)
                + (source_summary.pulse_response_count / total)
                + (source_summary.feedback_profile_count / total)
            )
            / 3
            * 100
        )
        return [
            TeamHealthStat(
                key="kpi_coverage",
                label="KPI Analiz Kapsami",
                value=f"{source_summary.kpi_analyzed_count}/{len(members)}",
                hint="KPI veya dataset kaydiyla hesaplanan calisan sayisi",
                tone="indigo",
            ),
            TeamHealthStat(
                key="pulse_average",
                label="Nabiz Ortalamasi",
                value=f"{avg_pulse}/5" if avg_pulse is not None else "Yok",
                hint="Son weekly pulse baglilik skoru",
                tone="blue",
            ),
            TeamHealthStat(
                key="feedback_coverage",
                label="360 Profil Kapsami",
                value=f"{source_summary.feedback_profile_count}/{len(members)}",
                hint="NLP profili uretilmis calisan sayisi",
                tone="emerald",
            ),
            TeamHealthStat(
                key="risk_candidates",
                label="Risk Toplantisi Adayi",
                value=str(risky_count),
                hint=f"{high_risk_count} yuksek risk, {max(risky_count - high_risk_count, 0)} orta risk",
                tone="rose" if high_risk_count else "amber" if risky_count else "emerald",
            ),
            TeamHealthStat(
                key="confidence",
                label="Veri Guveni",
                value=f"%{confidence}",
                hint="KPI, nabiz ve 360 kaynak kapsami",
                tone="slate",
            ),
        ]

    @staticmethod
    def update_employee(db: Session, emp_id: int, emp_data: EmployeeUpdate) -> Employee:
        employee = EmployeeService.get_employee_by_id(db, emp_id)

        if emp_data.department_id is not None:
            department = db.query(Department).filter(Department.id == emp_data.department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Departman bulunamadi (ID: {emp_data.department_id})",
                )

        if emp_data.external_employee_code is not None:
            EmployeeService._validate_external_employee_code(
                db,
                emp_data.external_employee_code,
                current_employee_id=employee.id,
            )

        update_data = emp_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def delete_employee(db: Session, emp_id: int) -> dict:
        employee = EmployeeService.get_employee_by_id(db, emp_id)

        if employee.kpi_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu calisana ait {len(employee.kpi_records)} KPI kaydi bulunuyor. "
                    "Once KPI kayitlarini silin."
                ),
            )

        if employee.survey_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu calisana ait {len(employee.survey_responses)} anket cevabi bulunuyor. "
                    "Once anket cevaplarini silin."
                ),
            )

        db.delete(employee)
        db.commit()
        return {"message": f"Calisan basariyla silindi (ID: {emp_id})"}
