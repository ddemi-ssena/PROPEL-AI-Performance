from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.services.department_service import DepartmentService

router = APIRouter()

@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni departman oluştur
    
    - **name**: Departman adı (zorunlu, benzersiz)
    - **description**: Departman açıklaması (opsiyonel)
    """
    return DepartmentService.create_department(db, dept_data)

@router.get("/", response_model=List[DepartmentResponse])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Tüm departmanları listele
    
    - **skip**: Atlanacak kayıt sayısı (pagination)
    - **limit**: Maksimum döndürülecek kayıt sayısı
    """
    return DepartmentService.get_all_departments(db, skip, limit)

@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(
    dept_id: int,
    db: Session = Depends(get_db)
):
    """
    ID'ye göre departman detayı getir
    """
    return DepartmentService.get_department_by_id(db, dept_id)

@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Departman bilgilerini güncelle
    """
    return DepartmentService.update_department(db, dept_id, dept_data)

@router.delete("/{dept_id}")
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db)
):
    """
    Departman sil (içinde çalışan yoksa)
    """
    return DepartmentService.delete_department(db, dept_id)