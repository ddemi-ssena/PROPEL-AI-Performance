from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.employee_service import EmployeeService

router = APIRouter()

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni çalışan oluştur
    
    - **user_id**: Kullanıcı ID'si (zorunlu, benzersiz)
    - **department_id**: Departman ID'si (zorunlu)
    - **position**: Pozisyon/Ünvan (opsiyonel)
    - **hire_date**: İşe giriş tarihi (opsiyonel, format: YYYY-MM-DD)
    """
    return EmployeeService.create_employee(db, emp_data)

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Tüm çalışanları listele
    """
    return EmployeeService.get_all_employees(db, skip, limit)

@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db)
):
    """
    ID'ye göre çalışan detayı getir
    """
    return EmployeeService.get_employee_by_id(db, emp_id)

@router.get("/department/{dept_id}", response_model=List[EmployeeResponse])
def get_employees_by_department(
    dept_id: int,
    db: Session = Depends(get_db)
):
    """
    Departmana göre çalışanları listele
    """
    return EmployeeService.get_employees_by_department(db, dept_id)

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: int,
    emp_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Çalışan bilgilerini güncelle
    """
    return EmployeeService.update_employee(db, emp_id, emp_data)

@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db)
):
    """
    Çalışan sil (ilişkili KPI ve anket verileri yoksa)
    """
    return EmployeeService.delete_employee(db, emp_id)