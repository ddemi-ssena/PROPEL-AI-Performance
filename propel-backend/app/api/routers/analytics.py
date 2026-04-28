from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.analytics import DepartmentAnalyticsConfigResponse, DepartmentAnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/departments", response_model=list[DepartmentAnalyticsConfigResponse])
def list_department_analytics_configs(
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.list_department_configs()


@router.get("/departments/{department_key}/overview", response_model=DepartmentAnalyticsOverviewResponse)
def get_department_analytics_overview(
    department_key: str,
    team: str | None = None,
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.get_department_overview(
        db=db,
        current_user=current_user,
        department_key=department_key,
        team=team,
        employee_id=employee_id,
    )
