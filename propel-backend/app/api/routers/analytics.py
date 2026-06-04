from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.analytics import (
    DepartmentAnalyticsConfigResponse,
    DepartmentAnalyticsOverviewResponse,
    DepartmentPerformanceSummaryResponse,
    SalesAllTargetsBulkResponse,
    SalesBulkPredictionResponse,
    SalesDatasetEmployeeResponse,
    SalesDatasetResponse,
    SalesEmployeePerformanceResponse,
    SalesModelStateResponse,
    SalesModelTrainRequest,
    SalesModelTrainResponse,
    SalesPredictionResponse,
    SoftwareBulkPredictionResponse,
    SoftwareDatasetEmployeeResponse,
    SoftwareDatasetResponse,
    SoftwareDepartmentDashboardResponse,
    SoftwareDepartmentInsightsResponse,
    SoftwareEmployeePerformanceResponse,
    SoftwareModelStateResponse,
    SoftwareModelTrainRequest,
    SoftwareModelTrainResponse,
    SoftwarePredictionResponse,
)
from app.schemas.team_report import TeamReportExportRequest
from app.services.analytics_service import AnalyticsService
from app.services.team_report_export_service import TeamReportExportService

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


@router.get("/departments/software/my-performance", response_model=SoftwareEmployeePerformanceResponse)
def get_my_software_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.get_my_performance(db=db, current_user=current_user)


@router.get("/departments/software/insights", response_model=SoftwareDepartmentInsightsResponse)
def get_software_department_insights(
    upload_id: int | None = None,
    period: str = "week",
    target_column: str = "performance_band",
    use_llm: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.generate_department_insights(
        db=db,
        upload_id=upload_id,
        period=period,
        target_column=target_column,
        use_llm=use_llm,
    )


@router.get("/departments/software/dashboard", response_model=SoftwareDepartmentDashboardResponse)
def get_software_department_dashboard(
    upload_id: int | None = None,
    period: str = "week",
    target_column: str = "performance_band",
    use_llm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.software_ml_service import SoftwareMLService

    return SoftwareMLService.generate_department_dashboard(
        db=db,
        current_user=current_user,
        upload_id=upload_id,
        period=period,
        target_column=target_column,
        use_llm=use_llm,
    )


@router.get("/performance/summary", response_model=DepartmentPerformanceSummaryResponse)
def get_performance_summary(
    department_id: int | None = None,
    team: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.get_performance_summary(
        db=db,
        current_user=current_user,
        department_id=department_id,
        team=team,
    )


@router.get("/departments/sales/datasets", response_model=list[SalesDatasetResponse])
def list_sales_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.list_datasets(db)


@router.get("/departments/sales/datasets/{upload_id}/employees", response_model=list[SalesDatasetEmployeeResponse])
def list_sales_dataset_employees(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.list_dataset_employees(db, upload_id)


@router.get("/departments/sales/datasets/{upload_id}/model-state", response_model=list[SalesModelStateResponse])
def list_sales_model_states(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.list_model_states(db, upload_id)


@router.post("/departments/sales/models/train", response_model=SalesModelTrainResponse)
def train_sales_model(
    payload: SalesModelTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.train_from_upload(
        db=db,
        upload_id=payload.upload_id,
        target_column=payload.target_column,
        test_period_count=payload.test_period_count,
    )


@router.get("/departments/sales/predictions/latest", response_model=SalesPredictionResponse)
def get_latest_sales_prediction(
    upload_id: int,
    employee_id: int,
    target_column: str = "Performance_Drop_Target",
    use_llm_narrative: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.predict_latest_from_upload(
        db=db,
        upload_id=upload_id,
        employee_id=employee_id,
        target_column=target_column,
        use_llm_narrative=use_llm_narrative,
    )


@router.get("/departments/sales/predictions/bulk", response_model=SalesBulkPredictionResponse)
def get_bulk_sales_predictions(
    upload_id: int,
    target_column: str = "Performance_Drop_Target",
    use_llm_narrative: bool = False,
    llm_team: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.predict_all_from_upload(
        db=db,
        upload_id=upload_id,
        target_column=target_column,
        use_llm_narrative=use_llm_narrative,
        llm_team=llm_team,
    )


@router.get("/departments/software/predictions/bulk-all-targets", response_model=SalesAllTargetsBulkResponse)
def get_bulk_software_all_targets(
    upload_id: int,
    use_llm_narrative: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yazılım departmanı 4 hedef toplu tahmin."""
    from app.services.software_ml_service import SoftwareMLService
    return SoftwareMLService.predict_all_targets(
        db=db,
        upload_id=upload_id,
        use_llm_narrative=use_llm_narrative,
    )


@router.get("/departments/sales/predictions/bulk-all-targets", response_model=SalesAllTargetsBulkResponse)
def get_bulk_sales_all_targets(
    upload_id: int,
    use_llm_narrative: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """4 hedef için toplu tahmin — feature engineering tek seferde yapılır."""
    from app.services.sales_ml_service import SalesMLService
    return SalesMLService.predict_all_targets(
        db=db,
        upload_id=upload_id,
        use_llm_narrative=use_llm_narrative,
    )


@router.get("/departments/sales/my-performance", response_model=SalesEmployeePerformanceResponse)
def get_my_sales_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.sales_ml_service import SalesMLService

    return SalesMLService.get_my_performance(db=db, current_user=current_user)


@router.post("/departments/software/team-report/export")
def export_software_team_report(
    payload: TeamReportExportRequest,
    current_user: User = Depends(get_current_user),
):
    stream = TeamReportExportService.build_workbook(payload)
    safe_team = "".join(char if char.isalnum() else "_" for char in payload.team).strip("_") or "Takim"
    safe_date = payload.report_date.replace(".", "_").replace("/", "_").replace(" ", "_")
    filename = f"{safe_team}_Takim_Analizi_{safe_date}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
