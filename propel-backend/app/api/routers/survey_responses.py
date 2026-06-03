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
    SurveyResponseDetailResponse,
    WeeklyPulseCreate
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

@router.post("/weekly-pulse", response_model=SurveyResponseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_weekly_pulse(
    pulse_data: WeeklyPulseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Haftalık Nabız Anketi (Weekly Pulse) doldur.
    ML Modeli (BERTürk) ile Zorluk, Başarı ve Öneri metinlerinden Motivasyon ve Ayrılma riski hesaplar (MTE & ARS).
    Sadece Employee rolündekiler doldurabilir ve sadece kendilerine.
    """
    if current_user.role != UserRole.employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu anketi yalnızca çalışanlar doldurabilir"
        )
        
    current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not current_employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Size ait bir çalışan kaydı bulunamadı"
        )
        
    # Güvenlik ve doğruluk için payload'ı asıl employee ID ile eziyoruz
    pulse_data.employee_id = current_employee.id
        
    return SurveyService.create_weekly_pulse_response(db, pulse_data)

@router.get("/analytics/insights")
def get_survey_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ML verilerini (MTE, ARS) yorumlayarak ön yüzdeki Dashboard analitiklerini (Kpi, Risk, Öneriler) doldurur.
    - Admin: Tüm veritabanı analizini çeker
    - Manager: Tüm departmanının analizini çeker
    """
    if current_user.role == UserRole.admin:
        responses = SurveyService.get_all_survey_responses(db, 0, 10000)
    elif current_user.role == UserRole.department_manager:
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Çalışan kaydınız bulunamadı")
        responses = SurveyService.get_responses_by_department(db, emp.department_id)
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Yetkisiz erişim")
        
    low_risk = 0
    med_risk = 0
    high_risk = 0
    total_mte = 0.0
    total_ms = 0.0
    
    for s in responses:
        ars = getattr(s, 'ars_score', None)
        if ars is not None:
            if ars >= 0.6:
                high_risk += 1
            elif ars >= 0.2:
                med_risk += 1
            else:
                low_risk += 1
        else:
            low_risk += 1
            
        mte = getattr(s, 'mte_score', None)
        if mte is not None:
            total_mte += mte
            
        total_ms += s.score
        
    count = len(responses) if len(responses) > 0 else 1
    avg_mte = total_mte / count
    avg_ms = total_ms / count
    
    # Dinamik Tavsiyeler (Recommendations)
    recs = []
    if high_risk > 0:
        recs.append({"title": "Tükenmişlik Riski Uyarısı", "description": f"{high_risk} çalışanda yüksek ayrılma ve tükenmişlik riski (ARS) tespit edildi. Acil görüşmeler planlayın.", "icon": "ExclamationCircleIcon"})
    if avg_mte < -0.1:
        recs.append({"title": "Genel Motivasyon Düşüşü", "description": "Açık uçlu anketlerden ekibin genel motivasyon trendinde (MTE) negatif eğilim gözlemleniyor. İş yükünü kontrol edin.", "icon": "ArrowTrendingDownIcon"})
    if avg_ms >= 4.0:
        recs.append({"title": "Yüksek Performans", "description": "Sayısal bağlılık skoru çok yüksek! Ekip uyumu harika durumda.", "icon": "MegaphoneIcon"})
    if not recs:
        recs.append({"title": "Stabil Gidişat", "description": "Ekip genel olarak dengeli ve stabil bir performans sergiliyor.", "icon": "LightBulbIcon"})
        
    return {
        "kpis": [
            {
                "title": "Ortalama Bağlılık (MS)",
                "value": f"{round(avg_ms, 1)}",
                "trend": "Aktif",
                "trendColor": "text-emerald-600",
                "comparison": "5 üzerinden"
            },
            {
                "title": "Motivasyon Eğilimi (MTE)",
                "value": f"{round(avg_mte, 3)}",
                "trend": "NLP Analizi",
                "trendColor": "text-blue-500",
                "comparison": "-1 ile +1 arası"
            },
            {
                "title": "Düşük Riskli Çalışan",
                "value": f"{low_risk}",
                "trend": "Güvenli",
                "trendColor": "text-emerald-600",
                "comparison": "toplam"
            },
            {
                "title": "Yüksek Riskli Çalışan",
                "value": f"{high_risk}",
                "trend": "Dikkat",
                "trendColor": "text-red-600",
                "comparison": "müdahale gerekli"
            }
        ],
        "riskData": [low_risk, med_risk, high_risk],
        "recommendations": recs
    }

@router.post("/analytics/gemini-insights")
def post_survey_gemini_insights(
    payload: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Frontend'den gelen filtrelenmiş anket verisini Gemini ile yorumla.
    Payload: { stats, sample_comments, dept_label }
    """
    from app.services.ai_service import AIService

    stats = payload.get("stats", {})
    sample_comments = payload.get("sample_comments", [])  # [{"name", "score", "mte", "ars", "challenge", "success", "suggestion"}]
    dept_label = payload.get("dept_label", "Tüm Departmanlar")

    if not stats:
        return {"narrative": None, "stats": {}, "gemini_used": False}

    # Yüksek ARS'li çalışanları öne çıkar
    risky = [c for c in sample_comments if (c.get("ars") or 0) >= 0.5]
    negative_mte = [c for c in sample_comments if (c.get("mte") or 0) < -0.1]

    # Gerçek yorumlardan alıntılar oluştur
    comment_block = ""
    if sample_comments:
        shown = sample_comments[:12]  # en fazla 12 kişi
        lines = []
        for c in shown:
            parts = [f"- {c.get('name','?')} (MS={c.get('score','?')}, MTE={c.get('mte','?')}, ARS={c.get('ars','?')})"]
            if c.get("challenge"):
                parts.append(f"  Zorluk: \"{c['challenge']}\"")
            if c.get("success"):
                parts.append(f"  Başarı: \"{c['success']}\"")
            if c.get("suggestion"):
                parts.append(f"  Öneri: \"{c['suggestion']}\"")
            lines.append("\n".join(parts))
        comment_block = "\n".join(lines)

    narrative = None
    if AIService.GEMINI_API_KEY:
        prompt = f"""Sen bir kurumsal İK ve çalışan deneyimi uzmanısın. Aşağıdaki HAFTALıK NABIZ ANKETİ verilerini analiz et ve Türkçe yönetici raporu hazırla.

## Kapsam: {dept_label}
Toplam yanıt: {stats.get('total', 0)} | Ortalama Bağlılık (MS): {stats.get('avg_ms', 0)}/5 | Motivasyon Trendi (MTE): {stats.get('avg_mte', 0)} | Ort. Ayrılma Riski (ARS): {stats.get('avg_ars', 0)}
Risk dağılımı: Yüksek={stats.get('high_risk', 0)}, Orta={stats.get('med_risk', 0)}, Düşük={stats.get('low_risk', 0)}
Negatif MTE (motivasyon düşüşü): {stats.get('neg_mte', 0)} kişi | Pozitif MTE: {stats.get('pos_mte', 0)} kişi

## Çalışan Yanıtları (Gerçek Veri)
{comment_block if comment_block else "(Yorum verisi yok)"}

## Yüksek Riskli / Negatif MTE'li Çalışanlar
{chr(10).join(f"- {c.get('name')} (ARS={c.get('ars')})" for c in risky[:5]) if risky else "Tespit edilmedi"}
{chr(10).join(f"- {c.get('name')} (MTE={c.get('mte')})" for c in negative_mte[:5]) if negative_mte else ""}

## Görev
SADECE şu 3 bölümü yaz. Her bölüm net ve kısa olsun:

### GENEL DURUM
(Yukarıdaki gerçek verilere göre ekibin durumunu 2-3 cümleyle özetle)

### ÖNE ÇIKAN RİSKLER
(Gerçek veriden tespit ettiğin en kritik 2-3 risk noktasını madde madde yaz)

### YÖNETİCİ İÇİN AKSİYONLAR
(Bu spesifik verilere göre 3-4 somut, uygulanabilir adım)

Türkçe, profesyonel yaz. Belirsiz genel ifadeler kullanma — verideki gerçek sayılara ve alıntılara atıfta bulun.
"""
        narrative = AIService._generate_with_gemini(prompt, timeout_seconds=30)

    return {"narrative": narrative, "stats": stats, "gemini_used": narrative is not None}


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