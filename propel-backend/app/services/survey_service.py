from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import date

from app.db.models.survey_response import SurveyResponse
from app.db.models.employee import Employee
from app.schemas.survey_response import SurveyResponseCreate, SurveyResponseUpdate, WeeklyPulseCreate

class SurveyService:
    
    # İzin verilen anket tipleri
    ALLOWED_SURVEY_TYPES = ["motivation", "satisfaction", "stress", "weekly_pulse"]
    
    @staticmethod
    def create_survey_response(db: Session, survey_data: SurveyResponseCreate) -> SurveyResponse:
        """Yeni anket cevabı oluştur"""
        
        # Survey type kontrolü
        if survey_data.survey_type not in SurveyService.ALLOWED_SURVEY_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz anket tipi. İzin verilenler: {', '.join(SurveyService.ALLOWED_SURVEY_TYPES)}"
            )
        
        # Employee var mı kontrol et
        employee = db.query(Employee).filter(Employee.id == survey_data.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {survey_data.employee_id})"
            )
        
        # Aynı çalışan, aynı anket tipi, aynı dönem için cevap var mı?
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.employee_id == survey_data.employee_id,
            SurveyResponse.survey_type == survey_data.survey_type,
            SurveyResponse.period_date == survey_data.period_date
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu çalışan bu anket için bu dönemde zaten cevap vermiş (ID: {existing.id})"
            )
        
        db_survey = SurveyResponse(**survey_data.dict())
        db.add(db_survey)
        db.commit()
        db.refresh(db_survey)
        return db_survey

    @staticmethod
    def create_weekly_pulse_response(db: Session, pulse_data: "WeeklyPulseCreate") -> SurveyResponse:
        from app.ml.prediction_engine import prediction_engine
        
        # 1. Employee kontrolü
        employee = db.query(Employee).filter(Employee.id == pulse_data.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {pulse_data.employee_id})"
            )
            
        # 2. Aynı dönem için anket var mı?
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.employee_id == pulse_data.employee_id,
            SurveyResponse.survey_type == "weekly_pulse",
            SurveyResponse.period_date == pulse_data.period_date
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu hafta için zaten nabız anketi doldurdunuz."
            )
            
        # 3. Sayısal hesaplamalar (MS)
        ms_score = round((pulse_data.q1 + pulse_data.q2 + pulse_data.q3) / 3, 2)
        
        # 4. ML Duygu Analizi (MTE, ARS)
        ml_results = prediction_engine.analyze_pulse_survey(
            q4_diff=pulse_data.q4,
            q5_succ=pulse_data.q5,
            q6_sugg=pulse_data.q6
        )
        
        # 5. DB'ye kaydet
        db_survey = SurveyResponse(
            employee_id=pulse_data.employee_id,
            survey_type="weekly_pulse",
            score=ms_score,
            period_date=pulse_data.period_date,
            comments="Weekly pulse open-ended answers stored in raw_data",
            raw_data=pulse_data.model_dump(mode='json'),
            mte_score=ml_results.get("mte_score"),
            ars_score=ml_results.get("ars_score")
        )
        
        db.add(db_survey)
        db.commit()
        db.refresh(db_survey)
        return db_survey
    
    @staticmethod
    def get_all_survey_responses(db: Session, skip: int = 0, limit: int = 100) -> List[SurveyResponse]:
        """Tüm anket cevaplarını listele"""
        return db.query(SurveyResponse).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_survey_response_by_id(db: Session, survey_id: int) -> SurveyResponse:
        """ID'ye göre anket cevabı getir"""
        survey = db.query(SurveyResponse).filter(SurveyResponse.id == survey_id).first()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anket cevabı bulunamadı (ID: {survey_id})"
            )
        return survey
    
    @staticmethod
    def get_responses_by_employee(db: Session, emp_id: int) -> List[SurveyResponse]:
        """Çalışana göre anket cevaplarını listele"""
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Çalışan bulunamadı (ID: {emp_id})"
            )
        
        return db.query(SurveyResponse).filter(SurveyResponse.employee_id == emp_id).all()
    
    @staticmethod
    def get_responses_by_type(db: Session, survey_type: str) -> List[SurveyResponse]:
        """Anket tipine göre cevapları listele"""
        if survey_type not in SurveyService.ALLOWED_SURVEY_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz anket tipi. İzin verilenler: {', '.join(SurveyService.ALLOWED_SURVEY_TYPES)}"
            )
        
        return db.query(SurveyResponse).filter(SurveyResponse.survey_type == survey_type).all()
    
    @staticmethod
    def get_responses_by_department(db: Session, dept_id: int) -> List[SurveyResponse]:
        """Departmana göre anket cevaplarını listele"""
        # Department üzerinden employees ve onların survey'lerini çek
        responses = db.query(SurveyResponse).join(Employee).filter(
            Employee.department_id == dept_id
        ).all()
        
        return responses
    
    @staticmethod
    def update_survey_response(db: Session, survey_id: int, survey_data: SurveyResponseUpdate) -> SurveyResponse:
        """Anket cevabını güncelle"""
        survey = SurveyService.get_survey_response_by_id(db, survey_id)
        
        update_data = survey_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(survey, field, value)
        
        db.commit()
        db.refresh(survey)
        return survey
    
    @staticmethod
    def delete_survey_response(db: Session, survey_id: int) -> dict:
        """Anket cevabını sil"""
        survey = SurveyService.get_survey_response_by_id(db, survey_id)
        
        db.delete(survey)
        db.commit()
        return {"message": f"Anket cevabı başarıyla silindi (ID: {survey_id})"}