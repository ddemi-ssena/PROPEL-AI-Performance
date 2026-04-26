from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.db.models.employee import Employee
from app.db.models.user import User
from app.db.models.department import Department
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

class EmployeeService:
    
    @staticmethod
    def create_employee(db: Session, emp_data: EmployeeCreate) -> Employee:
        """Yeni çalışan oluştur"""
        
        # User var mı kontrol et
        user = db.query(User).filter(User.id == emp_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kullanıcı bulunamadı (ID: {emp_data.user_id})"
            )
        
        # Bu user zaten bir çalışan mı?
        existing_employee = db.query(Employee).filter(Employee.user_id == emp_data.user_id).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu kullanıcı zaten bir çalışan olarak kayıtlı (Employee ID: {existing_employee.id})"
            )
        
        # Department var mı kontrol et
        department = db.query(Department).filter(Department.id == emp_data.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadı (ID: {emp_data.department_id})"
            )
        
        # Çalışan oluştur
        db_employee = Employee(**emp_data.dict())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    
    @staticmethod
    def _attach_latest_surveys(employees: List[Employee]) -> List[Employee]:
        for emp in employees:
            if getattr(emp, 'survey_responses', None) and len(emp.survey_responses) > 0:
                # Sort by period_date descending
                latest = sorted(emp.survey_responses, key=lambda x: x.period_date, reverse=True)[0]
                setattr(emp, 'latest_ms', latest.score)
                setattr(emp, 'latest_mte', getattr(latest, 'mte_score', None))
                setattr(emp, 'latest_ars', getattr(latest, 'ars_score', None))
                
                # Assign Risk Level
                ars = getattr(latest, 'ars_score', None)
                if ars is not None:
                    if ars >= 0.6:
                        setattr(emp, 'risk_level', "High")
                    elif ars >= 0.2:
                        setattr(emp, 'risk_level', "Medium")
                    else:
                        setattr(emp, 'risk_level', "Low")
                else:
                    setattr(emp, 'risk_level', "Low")
            else:
                setattr(emp, 'latest_ms', None)
                setattr(emp, 'latest_mte', None)
                setattr(emp, 'latest_ars', None)
                setattr(emp, 'risk_level', "Low")
        return employees

    @staticmethod
    def get_all_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Tüm çalışanları listele"""
        employees = db.query(Employee).offset(skip).limit(limit).all()
        return EmployeeService._attach_latest_surveys(employees)
    
    @staticmethod
    def get_employee_by_id(db: Session, emp_id: int) -> Employee:
        """ID'ye göre çalışan getir"""
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {emp_id})"
            )
        return EmployeeService._attach_latest_surveys([employee])[0]
    
    @staticmethod
    def get_employees_by_department(db: Session, dept_id: int) -> List[Employee]:
        """Departmana göre çalışanları listele"""
        # Önce department var mı kontrol et
        department = db.query(Department).filter(Department.id == dept_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadı (ID: {dept_id})"
            )
        
        employees = db.query(Employee).filter(Employee.department_id == dept_id).all()
        return EmployeeService._attach_latest_surveys(employees)
    
    @staticmethod
    def update_employee(db: Session, emp_id: int, emp_data: EmployeeUpdate) -> Employee:
        """Çalışan güncelle"""
        employee = EmployeeService.get_employee_by_id(db, emp_id)
        
        # Eğer department_id değiştiriliyorsa, yeni departman var mı kontrol et
        if emp_data.department_id is not None:
            department = db.query(Department).filter(Department.id == emp_data.department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Departman bulunamadı (ID: {emp_data.department_id})"
                )
        
        # Sadece gönderilen alanları güncelle
        update_data = emp_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        
        db.commit()
        db.refresh(employee)
        return employee
    
    @staticmethod
    def delete_employee(db: Session, emp_id: int) -> dict:
        """Çalışan sil"""
        employee = EmployeeService.get_employee_by_id(db, emp_id)
        
        # Çalışana ait KPI kayıtları varsa uyarı ver
        if employee.kpi_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu çalışana ait {len(employee.kpi_records)} KPI kaydı bulunuyor. Önce KPI kayıtlarını silin."
            )
        
        # Çalışana ait anket cevapları varsa uyarı ver
        if employee.survey_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu çalışana ait {len(employee.survey_responses)} anket cevabı bulunuyor. Önce anket cevaplarını silin."
            )
        
        db.delete(employee)
        db.commit()
        return {"message": f"Çalışan başarıyla silindi (ID: {emp_id})"}