import io
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_current_active_admin
from app.db.models.data_upload import DataUpload
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.data_upload import DataUploadResponse
from app.services.upload_service import UploadService

router = APIRouter()

_SOFTWARE_TEMPLATE = (
    "employee_id,week,year,gto,zto,gke,kkke,by,kbo,crko,performance_band,attrition_risk_band\n"
    "SW-001,1,2024,85,3,90,4.2,40,95,88,High,Low\n"
    "SW-002,1,2024,72,6,78,3.8,52,88,75,Medium,Medium\n"
)

_SALES_TEMPLATE = (
    "Employee_ID,Week,Year,Region,Role_Level,"
    "Total_Activity,Lead_to_Win_Conversion,Average_Sales_Cycle_Days,"
    "Sales_Workload_Index,Followup_OnTime_Rate,Customer_Satisfaction,"
    "CRM_Usage_Rate,Motivation_Score,Peer_Support_Count,"
    "Won_Deal_Count,Lost_Deal_Count,Revenue_Generated,Sales_Target,"
    "New_Customers,Total_Customers,Pipeline_Value,Pipeline_Aged,"
    "Open_Deals,Complaints,Mentor_Count,Training_Completed,Training_Recommended,"
    "Performance_Drop_Target,Burnout_Target,Resignation_Target,High_Risk_Target\n"
    "SA-001,1,2024,Marmara,Senior,"
    "42,0.35,28,6.2,0.88,4.3,0.91,7.5,3,"
    "8,4,85000,90000,5,60,120000,15000,"
    "22,1,2,4,5,"
    "0,0,0,0\n"
)


@router.get('/template')
def download_template(
    dept: str = Query(default='software', description='software veya sales'),
    current_user: User = Depends(get_current_active_admin),
):
    if dept == 'sales':
        content = _SALES_TEMPLATE
        filename = 'satis_kpi_sablon.csv'
    else:
        content = _SOFTWARE_TEMPLATE
        filename = 'yazilim_kpi_sablon.csv'

    return StreamingResponse(
        io.BytesIO(content.encode('utf-8-sig')),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.post('/', response_model=DataUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_data(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    department_key: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    return await UploadService.process_upload(db, file, file_type, current_user, department_key=department_key)


@router.get('/', response_model=List[DataUploadResponse])
def list_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    return UploadService.get_all_uploads(db, skip, limit)


@router.get('/{upload_id}', response_model=DataUploadResponse)
def get_upload_detail(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail='Yukleme kaydi bulunamadi')
    return upload
