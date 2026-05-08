from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.analytics import (
    DepartmentAnalyticsConfigResponse,
    DepartmentAnalyticsOverviewResponse,
    SoftwareBulkPredictionResponse,
    SoftwareDatasetEmployeeResponse,
    SoftwareDatasetResponse,
    SoftwareModelStateResponse,
    SoftwareModelTrainRequest,
    SoftwareModelTrainResponse,
    SoftwarePredictionResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/departments", response_model=list[DepartmentAnalyticsConfigResponse])
def list_department_analytics_configs(
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.list_department_configs(current_user)


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


@router.get("/departments/software/datasets", response_model=list[SoftwareDatasetResponse])
def list_software_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.list_datasets(db)


@router.get("/departments/software/datasets/{upload_id}/employees", response_model=list[SoftwareDatasetEmployeeResponse])
def list_software_dataset_employees(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.list_dataset_employees(db, upload_id)


@router.get("/departments/software/datasets/{upload_id}/model-state", response_model=list[SoftwareModelStateResponse])
def list_software_model_states(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.list_model_states(db, upload_id)


@router.post("/departments/software/models/train", response_model=SoftwareModelTrainResponse)
def train_software_model(
    payload: SoftwareModelTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.train_from_upload(
        db=db,
        upload_id=payload.upload_id,
        target_column=payload.target_column,
        model_name=payload.model_name,
        test_period_count=payload.test_period_count,
    )


@router.get("/departments/software/predictions/latest", response_model=SoftwarePredictionResponse)
def get_latest_software_prediction(
    upload_id: int,
    employee_id: int,
    target_column: str = "performance_band",
    use_llm_narrative: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.predict_latest_from_upload(
        db=db,
        upload_id=upload_id,
        employee_id=employee_id,
        target_column=target_column,
        use_llm_narrative=use_llm_narrative,
    )


@router.get("/departments/software/predictions/bulk", response_model=SoftwareBulkPredictionResponse)
def get_bulk_software_predictions(
    upload_id: int,
    target_column: str = "performance_band",
    use_llm_narrative: bool = False,
    llm_team: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.predict_all_from_upload(
        db=db,
        upload_id=upload_id,
        target_column=target_column,
        use_llm_narrative=use_llm_narrative,
        llm_team=llm_team,
    )
