from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.employee import Employee
from app.db.models.kpi import KPIRecord
from app.schemas.kpi import (
    KPICreate, KPIUpdate, KPIResponse,
    KPIRecordCreate, KPIRecordUpdate, KPIRecordResponse, KPIRecordDetailResponse
)
from app.services.kpi_service import KPIService
from app.api.dependencies import get_current_user, get_current_active_admin

router = APIRouter()

# ==================== KPI Endpoints ====================

@router.post("/", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
def create_kpi(
    kpi_data: KPICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Yeni KPI oluştur (Sadece Admin)"""
    return KPIService.create_kpi(db, kpi_data)


@router.get("/", response_model=List[KPIResponse])
def list_kpis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm KPI'ları listele"""
    return KPIService.get_all_kpis(db, skip, limit)


@router.get("/department/{dept_id}", response_model=List[KPIResponse])
def get_kpis_by_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Departmana göre KPI'ları listele"""
    return KPIService.get_kpis_by_department(db, dept_id)


# ==================== KPI Record Endpoints ====================

@router.post("/records", response_model=KPIRecordResponse, status_code=status.HTTP_201_CREATED)
def create_kpi_record(
    record_data: KPIRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.employee:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not current_employee:
            raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")
        if record_data.employee_id != current_employee.id:
            raise HTTPException(status_code=403, detail="Başka çalışanlar için KPI kaydı oluşturamazsınız")

    if current_user.role == UserRole.department_manager:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        target_employee = db.query(Employee).filter(Employee.id == record_data.employee_id).first()
        if not current_employee or not target_employee:
            raise HTTPException(status_code=404, detail="Çalışan kaydı bulunamadı")
        if target_employee.department_id != current_employee.department_id:
            raise HTTPException(status_code=403, detail="Farklı departmandaki çalışanlar için KPI kaydı oluşturamazsınız")

    return KPIService.create_kpi_record(db, record_data)


@router.get("/records", response_model=List[KPIRecordDetailResponse])
def list_kpi_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.admin:
        return KPIService.get_all_kpi_records(db, skip, limit)

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        dept_employee_ids = [
            e.id for e in db.query(Employee)
            .filter(Employee.department_id == employee.department_id)
            .all()
        ]

        return db.query(KPIRecord).filter(
            KPIRecord.employee_id.in_(dept_employee_ids)
        ).offset(skip).limit(limit).all()

    return KPIService.get_records_by_employee(db, employee.id)


@router.get("/records/{record_id}", response_model=KPIRecordDetailResponse)
def get_kpi_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = KPIService.get_kpi_record_by_id(db, record_id)

    if current_user.role == UserRole.admin:
        return record

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        record_employee = db.query(Employee).filter(Employee.id == record.employee_id).first()
        if not record_employee or record_employee.department_id != employee.department_id:
            raise HTTPException(status_code=403, detail="Bu KPI kaydını görüntüleme yetkiniz yok")
        return record

    if record.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Başka çalışanların KPI kayıtlarına erişemezsiniz")

    return record


@router.get("/records/employee/{emp_id}", response_model=List[KPIRecordDetailResponse])
def get_records_by_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.admin:
        return KPIService.get_records_by_employee(db, emp_id)

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        target_employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not target_employee or target_employee.department_id != employee.department_id:
            raise HTTPException(status_code=403, detail="Bu çalışanın KPI kayıtlarını görüntüleme yetkiniz yok")
        return KPIService.get_records_by_employee(db, emp_id)

    if emp_id != employee.id:
        raise HTTPException(status_code=403, detail="Başka çalışanların KPI kayıtlarına erişemezsiniz")

    return KPIService.get_records_by_employee(db, emp_id)


@router.get("/records/kpi/{kpi_id}", response_model=List[KPIRecordDetailResponse])
def get_records_by_kpi(
    kpi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.admin:
        return KPIService.get_records_by_kpi(db, kpi_id)

    all_records = KPIService.get_records_by_kpi(db, kpi_id)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        dept_ids = [
            e.id for e in db.query(Employee)
            .filter(Employee.department_id == employee.department_id)
            .all()
        ]
        return [r for r in all_records if r.employee_id in dept_ids]

    return [r for r in all_records if r.employee_id == employee.id]


@router.put("/records/{record_id}", response_model=KPIRecordResponse)
def update_kpi_record(
    record_id: int,
    record_data: KPIRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = KPIService.get_kpi_record_by_id(db, record_id)

    if current_user.role == UserRole.admin:
        return KPIService.update_kpi_record(db, record_id, record_data)

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        record_employee = db.query(Employee).filter(Employee.id == record.employee_id).first()
        if not record_employee or record_employee.department_id != employee.department_id:
            raise HTTPException(status_code=403, detail="Bu KPI kaydını güncelleme yetkiniz yok")
        return KPIService.update_kpi_record(db, record_id, record_data)

    if record.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Başka çalışanların KPI kayıtlarını güncelleyemezsiniz")

    return KPIService.update_kpi_record(db, record_id, record_data)


@router.delete("/records/{record_id}")
def delete_kpi_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = KPIService.get_kpi_record_by_id(db, record_id)

    if current_user.role == UserRole.admin:
        return KPIService.delete_kpi_record(db, record_id)

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Çalışan kaydınız bulunamadı")

    if current_user.role == UserRole.department_manager:
        record_employee = db.query(Employee).filter(Employee.id == record.employee_id).first()
        if not record_employee or record_employee.department_id != employee.department_id:
            raise HTTPException(status_code=403, detail="Bu KPI kaydını silme yetkiniz yok")
        return KPIService.delete_kpi_record(db, record_id)

    if record.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Başka çalışanların KPI kayıtlarını silemezsiniz")

    return KPIService.delete_kpi_record(db, record_id)


# ==================== DİNAMİK KPI ID — EN ALT ====================

@router.get("/{kpi_id}", response_model=KPIResponse)
def get_kpi(
    kpi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return KPIService.get_kpi_by_id(db, kpi_id)


@router.put("/{kpi_id}", response_model=KPIResponse)
def update_kpi(
    kpi_id: int,
    kpi_data: KPIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    return KPIService.update_kpi(db, kpi_id, kpi_data)


@router.delete("/{kpi_id}")
def delete_kpi(
    kpi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    return KPIService.delete_kpi(db, kpi_id)
