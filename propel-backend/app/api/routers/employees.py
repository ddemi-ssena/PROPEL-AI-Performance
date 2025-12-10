from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.employee_service import EmployeeService
from app.api.dependencies import get_current_user, get_current_active_admin, get_current_manager_or_admin

router = APIRouter()

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)  # ✅ Sadece Admin
):
    """Yeni çalışan oluştur (Sadece Admin)"""
    return EmployeeService.create_employee(db, emp_data)

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Çalışanları listele
    - Admin: Tüm çalışanlar
    - Manager: Kendi departmanındaki çalışanlar
    - Employee: Sadece kendisi
    """
    # ✅ Admin ise tümünü göster
    if current_user.role == UserRole.admin:
        return EmployeeService.get_all_employees(db, skip, limit)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise kendi departmanındakileri göster
    if current_user.role == UserRole.department_manager:
        return EmployeeService.get_employees_by_department(db, employee.department_id)
    
    # ✅ Employee ise sadece kendisini göster
    return [employee]

@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Çalışan detayı
    - Admin: Tüm çalışanlar
    - Manager: Kendi departmanındaki çalışanlar
    - Employee: Sadece kendisi
    """
    employee_record = EmployeeService.get_employee_by_id(db, emp_id)
    
    # ✅ Admin ise herhangi bir çalışanı görebilir
    if current_user.role == UserRole.admin:
        return employee_record
    
    # ✅ Kullanıcının kendi employee kaydını bul
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not current_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise sadece kendi departmanındakileri görebilir
    if current_user.role == UserRole.department_manager:
        if employee_record.department_id != current_employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu çalışanı görüntüleme yetkiniz yok"
            )
        return employee_record
    
    # ✅ Employee ise sadece kendisini görebilir
    if employee_record.id != current_employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka çalışanların bilgilerine erişemezsiniz"
        )
    
    return employee_record

@router.get("/department/{dept_id}", response_model=List[EmployeeResponse])
def get_employees_by_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)  # ✅ Manager veya Admin
):
    """
    Departmana göre çalışanları listele (Manager veya Admin)
    """
    # ✅ Manager ise sadece kendi departmanını görebilir
    if current_user.role == UserRole.department_manager:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee or employee.department_id != dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu departmanın çalışanlarını görüntüleme yetkiniz yok"
            )
    
    return EmployeeService.get_employees_by_department(db, dept_id)

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: int,
    emp_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)  # ✅ Sadece Admin
):
    """Çalışan güncelle (Sadece Admin)"""
    return EmployeeService.update_employee(db, emp_id, emp_data)

@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)  # ✅ Sadece Admin
):
    """Çalışan sil (Sadece Admin)"""
    return EmployeeService.delete_employee(db, emp_id)