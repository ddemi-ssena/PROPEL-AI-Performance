from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.employee import Employee
from app.schemas.survey_response import (
    SurveyResponseCreate, 
    SurveyResponseUpdate, 
    SurveyResponseResponse,
    SurveyResponseDetailResponse
)
from app.services.survey_service import SurveyService
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=SurveyResponseResponse, status_code=status.HTTP_201_CREATED)
def create_survey_response(
    survey_data: SurveyResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket cevabı oluştur
    - Admin/Manager: Kendi departmanındaki çalışanlar için
    - Employee: Sadece kendisi için
    """
    # ✅ Employee ise sadece kendisi için cevap oluşturabilir
    if current_user.role == UserRole.employee:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not current_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Çalışan kaydınız bulunamadı"
            )
        
        if survey_data.employee_id != current_employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Başka çalışanlar için anket cevabı oluşturamazsınız"
            )
    
    # ✅ Manager ise sadece kendi departmanındaki çalışanlar için oluşturabilir
    if current_user.role == UserRole.department_manager:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        target_employee = db.query(Employee).filter(Employee.id == survey_data.employee_id).first()
        
        if not current_employee or not target_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Çalışan kaydı bulunamadı"
            )
        
        if target_employee.department_id != current_employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farklı departmandaki çalışanlar için anket cevabı oluşturamazsınız"
            )
    
    return SurveyService.create_survey_response(db, survey_data)

@router.get("/", response_model=List[SurveyResponseDetailResponse])
def list_survey_responses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket cevaplarını listele
    - Admin: Tümü
    - Manager: Kendi departmanı
    - Employee: Sadece kendisi
    """
    # ✅ Admin ise tümünü göster
    if current_user.role == UserRole.admin:
        return SurveyService.get_all_survey_responses(db, skip, limit)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise kendi departmanındakilerin anketlerini göster
    if current_user.role == UserRole.department_manager:
        return SurveyService.get_responses_by_department(db, employee.department_id)
    
    # ✅ Employee ise sadece kendi cevaplarını göster
    return SurveyService.get_responses_by_employee(db, employee.id)

@router.get("/{survey_id}", response_model=SurveyResponseDetailResponse)
def get_survey_response(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket cevabı detayı
    - Admin: Tümü
    - Manager: Kendi departmanı
    - Employee: Sadece kendisi
    """
    survey = SurveyService.get_survey_response_by_id(db, survey_id)
    
    # ✅ Admin ise tümünü görebilir
    if current_user.role == UserRole.admin:
        return survey
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise sadece kendi departmanındakilerin cevaplarını görebilir
    if current_user.role == UserRole.department_manager:
        survey_employee = db.query(Employee).filter(Employee.id == survey.employee_id).first()
        if not survey_employee or survey_employee.department_id != employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu anket cevabını görüntüleme yetkiniz yok"
            )
        return survey
    
    # ✅ Employee ise sadece kendi cevaplarını görebilir
    if survey.employee_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka çalışanların anket cevaplarına erişemezsiniz"
        )
    
    return survey

@router.get("/employee/{emp_id}", response_model=List[SurveyResponseDetailResponse])
def get_responses_by_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Çalışana göre anket cevapları
    - Admin: Herhangi bir çalışan
    - Manager: Kendi departmanındaki çalışanlar
    - Employee: Sadece kendisi
    """
    # ✅ Admin ise herhangi bir çalışanın cevaplarını görebilir
    if current_user.role == UserRole.admin:
        return SurveyService.get_responses_by_employee(db, emp_id)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise sadece kendi departmanındakilerin cevaplarını görebilir
    if current_user.role == UserRole.department_manager:
        target_employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not target_employee or target_employee.department_id != employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu çalışanın anket cevaplarını görüntüleme yetkiniz yok"
            )
        return SurveyService.get_responses_by_employee(db, emp_id)
    
    # ✅ Employee ise sadece kendi cevaplarını görebilir
    if emp_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka çalışanların anket cevaplarına erişemezsiniz"
        )
    
    return SurveyService.get_responses_by_employee(db, emp_id)

@router.get("/type/{survey_type}", response_model=List[SurveyResponseDetailResponse])
def get_responses_by_type(
    survey_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket tipine göre cevapları listele
    - Admin: Tüm anketler
    - Manager: Kendi departmanının anketleri
    - Employee: Kendi anketleri
    """
    # ✅ Admin ise tüm anket tiplerini görebilir
    if current_user.role == UserRole.admin:
        return SurveyService.get_responses_by_type(db, survey_type)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # Tipe göre tüm cevapları al
    all_responses = SurveyService.get_responses_by_type(db, survey_type)
    
    # ✅ Manager ise sadece kendi departmanındakileri filtrele
    if current_user.role == UserRole.department_manager:
        dept_employee_ids = [e.id for e in db.query(Employee).filter(
            Employee.department_id == employee.department_id
        ).all()]
        
        filtered_responses = [r for r in all_responses if r.employee_id in dept_employee_ids]
        return filtered_responses
    
    # ✅ Employee ise sadece kendi cevaplarını filtrele
    filtered_responses = [r for r in all_responses if r.employee_id == employee.id]
    return filtered_responses

@router.get("/department/{dept_id}", response_model=List[SurveyResponseDetailResponse])
def get_responses_by_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Departmana göre anket cevaplarını listele
    - Admin: Herhangi bir departman
    - Manager: Sadece kendi departmanı
    - Employee: Erişim yok
    """
    # ✅ Employee departman bazlı anketlere erişemez
    if current_user.role == UserRole.employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Departman bazlı anket verilerine erişim yetkiniz yok"
        )
    
    # ✅ Admin ise herhangi bir departmanın anketlerini görebilir
    if current_user.role == UserRole.admin:
        return SurveyService.get_responses_by_department(db, dept_id)
    
    # ✅ Manager ise sadece kendi departmanının anketlerini görebilir
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    if employee.department_id != dept_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu departmanın anket cevaplarını görüntüleme yetkiniz yok"
        )
    
    return SurveyService.get_responses_by_department(db, dept_id)

@router.put("/{survey_id}", response_model=SurveyResponseResponse)
def update_survey_response(
    survey_id: int,
    survey_data: SurveyResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket cevabını güncelle
    - Admin: Tüm anketler
    - Manager: Kendi departmanının anketleri
    - Employee: Sadece kendi anketleri
    """
    survey = SurveyService.get_survey_response_by_id(db, survey_id)
    
    # ✅ Admin ise tümünü güncelleyebilir
    if current_user.role == UserRole.admin:
        return SurveyService.update_survey_response(db, survey_id, survey_data)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise sadece kendi departmanındakilerin anketlerini güncelleyebilir
    if current_user.role == UserRole.department_manager:
        survey_employee = db.query(Employee).filter(Employee.id == survey.employee_id).first()
        if not survey_employee or survey_employee.department_id != employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu anket cevabını güncelleme yetkiniz yok"
            )
        return SurveyService.update_survey_response(db, survey_id, survey_data)
    
    # ✅ Employee ise sadece kendi anketlerini güncelleyebilir
    if survey.employee_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka çalışanların anket cevaplarını güncelleyemezsiniz"
        )
    
    return SurveyService.update_survey_response(db, survey_id, survey_data)

@router.delete("/{survey_id}")
def delete_survey_response(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Anket cevabını sil
    - Admin: Tüm anketler
    - Manager: Kendi departmanının anketleri
    - Employee: Sadece kendi anketleri
    """
    survey = SurveyService.get_survey_response_by_id(db, survey_id)
    
    # ✅ Admin ise tümünü silebilir
    if current_user.role == UserRole.admin:
        return SurveyService.delete_survey_response(db, survey_id)
    
    # ✅ Kullanıcının employee kaydını bul
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Çalışan kaydınız bulunamadı"
        )
    
    # ✅ Manager ise sadece kendi departmanındakilerin anketlerini silebilir
    if current_user.role == UserRole.department_manager:
        survey_employee = db.query(Employee).filter(Employee.id == survey.employee_id).first()
        if not survey_employee or survey_employee.department_id != employee.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu anket cevabını silme yetkiniz yok"
            )
        return SurveyService.delete_survey_response(db, survey_id)
    
    # ✅ Employee ise sadece kendi anketlerini silebilir
    if survey.employee_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka çalışanların anket cevaplarını silemezsiniz"
        )
    
    return SurveyService.delete_survey_response(db, survey_id)