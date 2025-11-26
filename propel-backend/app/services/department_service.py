from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.db.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate

class DepartmentService:
    
    @staticmethod
    def create_department(db: Session, dept_data: DepartmentCreate) -> Department:
        """Yeni departman oluştur"""
        # Aynı isimde departman var mı kontrol et
        existing = db.query(Department).filter(Department.name == dept_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{dept_data.name}' isimli departman zaten mevcut"
            )
        
        db_dept = Department(**dept_data.dict())
        db.add(db_dept)
        db.commit()
        db.refresh(db_dept)
        return db_dept
    
    @staticmethod
    def get_all_departments(db: Session, skip: int = 0, limit: int = 100) -> List[Department]:
        """Tüm departmanları listele"""
        return db.query(Department).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_department_by_id(db: Session, dept_id: int) -> Department:
        """ID'ye göre departman getir"""
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadı (ID: {dept_id})"
            )
        return dept
    
    @staticmethod
    def update_department(db: Session, dept_id: int, dept_data: DepartmentUpdate) -> Department:
        """Departman güncelle"""
        dept = DepartmentService.get_department_by_id(db, dept_id)
        
        # Sadece gönderilen alanları güncelle
        update_data = dept_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)
        
        db.commit()
        db.refresh(dept)
        return dept
    
    @staticmethod
    def delete_department(db: Session, dept_id: int) -> dict:
        """Departman sil"""
        dept = DepartmentService.get_department_by_id(db, dept_id)
        
        # Departmanda çalışan varsa silinemez
        if dept.employees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu departmanda {len(dept.employees)} çalışan bulunuyor. Önce çalışanları transfer edin."
            )
        
        db.delete(dept)
        db.commit()
        return {"message": f"'{dept.name}' departmanı başarıyla silindi"}