from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.employee import Employee
from app.db.models.user import User, UserRole
from app.db.models.nlp import NLPPeriodType
from app.api.dependencies import get_current_employee_record, get_current_user
from app.schemas.feedbacks import (
    CurrentQuestionResponse,
    SubmitFeedbackPayload,
    SubmitFeedbackResponse,
    WeeklyProgressResponse,
    WeeklyAssignmentStateResponse,
    WeeklyAssignmentTargetResponse,
    WeeklyNLPInsightResponse,
    DepartmentWeeklyNLPResponse,
    Employee360SummaryReportResponse,
    Department360SummaryReportResponse,
    DepartmentNLPChartsResponse,
    EmployeeMonthlyDeepAnalysisResponse,
    DepartmentMonthlyDeepAnalysisResponse,
    EmployeeMonthlyRAGReportResponse,
    DepartmentMonthlyRAGReportResponse,
)
from app.services.feedback_service import FeedbackService
from app.services.nlp_service import NLPService

router = APIRouter()


def _can_access_employee_nlp(current_user: User, current_employee: Employee | None, target_employee: Employee) -> bool:
    if current_user.role == UserRole.admin:
        return True
    if current_user.role == UserRole.department_manager and current_employee:
        return current_employee.department_id == target_employee.department_id
    if current_employee:
        return current_employee.id == target_employee.id
    return False


@router.get("/assignment", response_model=WeeklyAssignmentStateResponse)
def get_weekly_assignment_state(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    state = FeedbackService.get_weekly_assignment_state(
        db,
        current_employee_id=current_employee.id,
    )

    mandatory_assignment = state.get("mandatory_assignment")
    mandatory_payload = None
    if mandatory_assignment and mandatory_assignment.target:
        mandatory_payload = WeeklyAssignmentTargetResponse(
            id=mandatory_assignment.id,
            status=mandatory_assignment.status.value,
            assignment_type=mandatory_assignment.assignment_type.value,
            employee=mandatory_assignment.target,
        )

    return WeeklyAssignmentStateResponse(
        week_number=state["week_number"],
        required_count=state["required_count"],
        completed_count=state["completed_count"],
        remaining_count=state["remaining_count"],
        is_completed=state["is_completed"],
        current_slot=state["current_slot"],
        assignment_required=state["assignment_required"],
        mandatory_assignment=mandatory_payload,
        available_candidates=state["available_candidates"],
        department_candidates=state["department_candidates"],
        cross_functional_candidates=state["cross_functional_candidates"],
        rules_summary=state["rules_summary"],
    )


@router.get("/current-question", response_model=CurrentQuestionResponse)
def get_current_question(
    receiver_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    question = FeedbackService.get_current_weekly_question(
        db,
        sender_employee_id=current_employee.id,
        receiver_employee_id=receiver_id,
    )
    return CurrentQuestionResponse(
        question_id=question.id,
        week_number=question.week_number,
        category=question.category,
        direction=question.direction,
        question_text=question.question_text,
        is_ai_generated=question.is_ai_generated,
    )


@router.post("/submit", response_model=SubmitFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_weekly_feedback(
    payload: SubmitFeedbackPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    row = FeedbackService.submit_weekly_feedback(
        db,
        sender_employee_id=current_employee.id,
        receiver_employee_id=payload.receiver_id,
        response_text=payload.response_text,
        score_communication=payload.score_communication,
        score_teamwork=payload.score_teamwork,
        score_leadership=payload.score_leadership,
        score_technical=payload.score_technical,
        process_nlp_sync=False,
    )
    background_tasks.add_task(
        FeedbackService.process_weekly_feedback_analysis_in_background,
        row.id,
    )
    return row


@router.get("/weekly-progress", response_model=WeeklyProgressResponse)
def get_weekly_progress(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    completed = FeedbackService.count_weekly_feedbacks(db, current_employee.id)
    required = 3
    remaining = max(required - completed, 0)
    return WeeklyProgressResponse(
        week_number=FeedbackService.get_week_of_month(),
        required_count=required,
        completed_count=completed,
        remaining_count=remaining,
        is_completed=completed >= required,
    )


@router.get("/progress", response_model=WeeklyProgressResponse)
def get_progress_alias(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    completed = FeedbackService.count_weekly_feedbacks(db, current_employee.id)
    required = 3
    remaining = max(required - completed, 0)
    return WeeklyProgressResponse(
        week_number=FeedbackService.get_week_of_month(),
        required_count=required,
        completed_count=completed,
        remaining_count=remaining,
        is_completed=completed >= required,
    )


@router.get("/nlp/me", response_model=WeeklyNLPInsightResponse)
def get_my_weekly_nlp_profile(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee_record),
):
    now = datetime.utcnow()
    week_number = FeedbackService.get_week_of_month(now.date())
    profile = NLPService.get_or_build_employee_profile(
        db,
        employee_id=current_employee.id,
        period_type=NLPPeriodType.weekly,
        period_year=now.year,
        period_month=now.month,
        period_week=week_number,
    )
    analyses = NLPService.get_recent_weekly_analyses(db, employee_id=current_employee.id, limit=5)
    return WeeklyNLPInsightResponse(profile=profile, recent_analyses=analyses)


@router.get("/nlp/employee/{employee_id}", response_model=WeeklyNLPInsightResponse)
def get_employee_weekly_nlp_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Calisan bulunamadi")

    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not _can_access_employee_nlp(current_user, current_employee, target_employee):
        raise HTTPException(status_code=403, detail="Bu calisanin NLP profiline erisim yetkiniz yok")

    now = datetime.utcnow()
    week_number = FeedbackService.get_week_of_month(now.date())
    profile = NLPService.get_or_build_employee_profile(
        db,
        employee_id=target_employee.id,
        period_type=NLPPeriodType.weekly,
        period_year=now.year,
        period_month=now.month,
        period_week=week_number,
    )
    analyses = NLPService.get_recent_weekly_analyses(db, employee_id=target_employee.id, limit=10)
    return WeeklyNLPInsightResponse(profile=profile, recent_analyses=analyses)


@router.get("/nlp/department-summary", response_model=DepartmentWeeklyNLPResponse)
def get_department_weekly_nlp_summary(
    department_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    if current_user.role == UserRole.department_manager:
        if not current_employee:
            raise HTTPException(status_code=404, detail="Calisan kaydi bulunamadi")
        target_department_id = current_employee.department_id
        if department_id and department_id != target_department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmaninizin NLP ozetine erisebilirsiniz")
    elif current_user.role == UserRole.admin:
        target_department_id = department_id or (current_employee.department_id if current_employee else None)
        if target_department_id is None:
            raise HTTPException(status_code=400, detail="Admin icin department_id gerekli")
    else:
        raise HTTPException(status_code=403, detail="Bu endpoint sadece manager veya admin icindir")

    now = datetime.utcnow()
    week_number = FeedbackService.get_week_of_month(now.date())
    summary = NLPService.get_department_weekly_summary(
        db,
        department_id=target_department_id,
        period_year=now.year,
        period_month=now.month,
        period_week=week_number,
    )
    return DepartmentWeeklyNLPResponse(**summary)


@router.get("/reports/employee/{employee_id}", response_model=Employee360SummaryReportResponse)
def get_employee_360_summary_report(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Calisan bulunamadi")

    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not _can_access_employee_nlp(current_user, current_employee, target_employee):
        raise HTTPException(status_code=403, detail="Bu calisanin 360 ozet raporuna erisim yetkiniz yok")

    now = datetime.utcnow()
    week_number = FeedbackService.get_week_of_month(now.date())
    report = NLPService.build_employee_360_summary_report(
        db,
        employee_id=target_employee.id,
        period_year=now.year,
        period_month=now.month,
        period_week=week_number,
    )
    return Employee360SummaryReportResponse(**report)


@router.get("/reports/employee/{employee_id}/monthly-deep", response_model=EmployeeMonthlyDeepAnalysisResponse)
def get_employee_monthly_deep_analysis(
    employee_id: int,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Calisan bulunamadi")

    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not _can_access_employee_nlp(current_user, current_employee, target_employee):
        raise HTTPException(status_code=403, detail="Bu calisanin aylik NLP analizine erisim yetkiniz yok")

    now = datetime.utcnow()
    target_year = year or now.year
    target_month = month or now.month

    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="month 1 ile 12 arasinda olmali")

    report = NLPService.build_employee_monthly_deep_analysis(
        db,
        employee_id=target_employee.id,
        period_year=target_year,
        period_month=target_month,
    )
    return EmployeeMonthlyDeepAnalysisResponse(**report)


@router.get("/reports/employee/{employee_id}/monthly-rag", response_model=EmployeeMonthlyRAGReportResponse)
def get_employee_monthly_rag_report(
    employee_id: int,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Calisan bulunamadi")

    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not _can_access_employee_nlp(current_user, current_employee, target_employee):
        raise HTTPException(status_code=403, detail="Bu calisanin aylik RAG analizine erisim yetkiniz yok")

    now = datetime.utcnow()
    target_year = year or now.year
    target_month = month or now.month
    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="month 1 ile 12 arasinda olmali")

    report = NLPService.build_employee_monthly_rag_report(
        db,
        employee_id=target_employee.id,
        period_year=target_year,
        period_month=target_month,
    )
    return EmployeeMonthlyRAGReportResponse(**report)


@router.get("/reports/department", response_model=Department360SummaryReportResponse)
def get_department_360_summary_report(
    department_id: int | None = None,
    team: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    if current_user.role == UserRole.department_manager:
        if not current_employee:
            raise HTTPException(status_code=404, detail="Calisan kaydi bulunamadi")
        target_department_id = current_employee.department_id
        if department_id and department_id != target_department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmaninizin 360 ozet raporuna erisebilirsiniz")
    elif current_user.role == UserRole.admin:
        target_department_id = department_id or (current_employee.department_id if current_employee else None)
        if target_department_id is None:
            raise HTTPException(status_code=400, detail="Admin icin department_id gerekli")
    else:
        raise HTTPException(status_code=403, detail="Bu endpoint sadece manager veya admin icindir")

    now = datetime.utcnow()
    week_number = FeedbackService.get_week_of_month(now.date())
    report = NLPService.build_department_360_summary_report(
        db,
        department_id=target_department_id,
        period_year=now.year,
        period_month=now.month,
        period_week=week_number,
        team=team,
    )
    return Department360SummaryReportResponse(**report)


@router.get("/reports/department/monthly-deep", response_model=DepartmentMonthlyDeepAnalysisResponse)
def get_department_monthly_deep_analysis(
    department_id: int | None = None,
    team: str | None = None,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    if current_user.role == UserRole.department_manager:
        if not current_employee:
            raise HTTPException(status_code=404, detail="Calisan kaydi bulunamadi")
        target_department_id = current_employee.department_id
        if department_id and department_id != target_department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmaninizin aylik NLP analizine erisebilirsiniz")
    elif current_user.role == UserRole.admin:
        target_department_id = department_id or (current_employee.department_id if current_employee else None)
        if target_department_id is None:
            raise HTTPException(status_code=400, detail="Admin icin department_id gerekli")
    else:
        raise HTTPException(status_code=403, detail="Bu endpoint sadece manager veya admin icindir")

    now = datetime.utcnow()
    target_year = year or now.year
    target_month = month or now.month

    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="month 1 ile 12 arasinda olmali")

    report = NLPService.build_department_monthly_deep_analysis(
        db,
        department_id=target_department_id,
        period_year=target_year,
        period_month=target_month,
        team=team,
    )
    return DepartmentMonthlyDeepAnalysisResponse(**report)


@router.get("/reports/department/monthly-rag", response_model=DepartmentMonthlyRAGReportResponse)
def get_department_monthly_rag_report(
    department_id: int | None = None,
    team: str | None = None,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    if current_user.role == UserRole.department_manager:
        if not current_employee:
            raise HTTPException(status_code=404, detail="Calisan kaydi bulunamadi")
        target_department_id = current_employee.department_id
        if department_id and department_id != target_department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmaninizin aylik RAG analizine erisebilirsiniz")
    elif current_user.role == UserRole.admin:
        target_department_id = department_id or (current_employee.department_id if current_employee else None)
        if target_department_id is None:
            raise HTTPException(status_code=400, detail="Admin icin department_id gerekli")
    else:
        raise HTTPException(status_code=403, detail="Bu endpoint sadece manager veya admin icindir")

    now = datetime.utcnow()
    target_year = year or now.year
    target_month = month or now.month
    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="month 1 ile 12 arasinda olmali")

    report = NLPService.build_department_monthly_rag_report(
        db,
        department_id=target_department_id,
        period_year=target_year,
        period_month=target_month,
        team=team,
    )
    return DepartmentMonthlyRAGReportResponse(**report)


@router.get("/charts/department", response_model=DepartmentNLPChartsResponse)
def get_department_nlp_charts(
    department_id: int | None = None,
    team: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    if current_user.role == UserRole.department_manager:
        if not current_employee:
            raise HTTPException(status_code=404, detail="Calisan kaydi bulunamadi")
        target_department_id = current_employee.department_id
        if department_id and department_id != target_department_id:
            raise HTTPException(status_code=403, detail="Sadece kendi departmaninizin NLP grafiklerine erisebilirsiniz")
    elif current_user.role == UserRole.admin:
        target_department_id = department_id or (current_employee.department_id if current_employee else None)
        if target_department_id is None:
            raise HTTPException(status_code=400, detail="Admin icin department_id gerekli")
    else:
        raise HTTPException(status_code=403, detail="Bu endpoint sadece manager veya admin icindir")

    now = datetime.utcnow()
    charts = NLPService.build_department_nlp_charts(
        db,
        department_id=target_department_id,
        period_year=now.year,
        period_month=now.month,
        team=team,
    )
    return DepartmentNLPChartsResponse(**charts)
