import io
from collections import defaultdict
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app.api.dependencies import get_current_active_admin
from app.db.models.data_upload import DataUpload
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackResponse
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.data_upload import DataUploadResponse
from app.services.upload_service import UploadService


# ── ONA Şemaları ──────────────────────────────────────────────────────────────

class OnaNode(BaseModel):
    id: int
    name: str
    employee_count: int
    centrality: float        # 0–1 arası, çapraz-dept etkileşim oranı
    is_silo: bool
    internal_count: int      # kendi içindeki etkileşim
    external_count: int      # diğer departmanlarla etkileşim


class OnaEdge(BaseModel):
    source_id: int
    target_id: int
    weight: int              # etkileşim sayısı
    strength: str            # "strong" | "medium" | "weak"


class OnaSummary(BaseModel):
    total_interactions: int
    cross_dept_interactions: int
    most_central_dept: Optional[str]
    silos: List[str]
    bridges: List[str]


class OnaResponse(BaseModel):
    nodes: List[OnaNode]
    edges: List[OnaEdge]
    summary: OnaSummary
    data_source: str   # "feedback" | "inferred" | "mixed"


class FlightRiskEmployee(BaseModel):
    employee_code: str
    employee_name: Optional[str] = None
    department: str
    position: Optional[str] = None
    team: Optional[str] = None
    risk_level: str          # "High" | "Medium" | "Low"
    risk_score: int          # 0-100
    performance_score: int   # 0-100, ML'den hesaplanan performans skoru
    confidence: float
    top_driver: Optional[str] = None
    predicted_band: str


class FlightRiskResponse(BaseModel):
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    employees: List[FlightRiskEmployee]

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


@router.get('/flight-risk', response_model=FlightRiskResponse)
def get_flight_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """ML modellerinden uçuş riski (istifa+performans) olan çalışanları döndürür."""
    employees: list[FlightRiskEmployee] = []

    # ── 1. SATIŞ departmanı ─────────────────────────────────────────────
    try:
        from app.services.sales_ml_service import SalesMLService
        sales_datasets = SalesMLService.list_datasets(db)
        if sales_datasets:
            upload_id = sales_datasets[0].id

            # Birden fazla hedef çalıştır; en kötü skoru al
            sales_risk_map: dict[int, dict] = {}
            for target_col, weight in [
                ("Performance_Drop_Target", 1.0),
                ("Resignation_Target", 1.2),   # uçuş riskini daha ağırlıklı say
                ("High_Risk_Target", 0.8),
            ]:
                try:
                    b = SalesMLService.predict_all_from_upload(
                        db=db, upload_id=upload_id,
                        target_column=target_col, use_llm_narrative=False,
                    )
                    for item in b.items:
                        eid = item.employee_id
                        band = str(item.predicted_band)
                        base_score = int(round(item.confidence * 100)) if band == "1" else int(round((1 - item.confidence) * 100))
                        weighted = int(base_score * weight) if band == "1" else 0
                        existing = sales_risk_map.get(eid, {})
                        # en yüksek ağırlıklı skoru sakla
                        if weighted > existing.get("weighted", 0):
                            sales_risk_map[eid] = {
                                "item": item,
                                "band": band,
                                "weighted": weighted,
                                "risk_score": base_score,
                            }
                        elif eid not in sales_risk_map:
                            sales_risk_map[eid] = {
                                "item": item,
                                "band": band,
                                "weighted": 0,
                                "risk_score": base_score,
                            }
                except Exception:
                    pass

            for eid, data in sales_risk_map.items():
                item = data["item"]
                band = data["band"]
                risk_pct = data["risk_score"]
                if data["weighted"] >= 60:
                    risk_level = "High"
                    risk_score = max(60, risk_pct)
                else:
                    risk_level = "Low"
                    risk_score = min(40, risk_pct)

                # Performans skoru: band=0 (iyi) → 55-95, band=1 (riskli) → 15-50
                conf = item.confidence
                if band == "0":
                    perf_score = min(95, max(55, round(55 + conf * 40)))
                else:
                    perf_score = min(50, max(15, round(50 - conf * 35)))

                top_driver = None
                if item.top_drivers:
                    top_driver = item.top_drivers[0].get("metric_name")

                employees.append(FlightRiskEmployee(
                    employee_code=item.summary_payload.get("external_employee_code") or f"SA-{item.employee_id:03d}",
                    employee_name=item.summary_payload.get("employee_name"),
                    department="Satis",
                    position=item.summary_payload.get("position"),
                    team=item.summary_payload.get("team"),
                    risk_level=risk_level,
                    risk_score=risk_score,
                    performance_score=perf_score,
                    confidence=item.confidence,
                    top_driver=top_driver,
                    predicted_band=band,
                ))
    except Exception:
        pass

    # ── 2. YAZILIM departmanı ────────────────────────────────────────────
    try:
        from app.services.software_ml_service import SoftwareMLService

        sw_datasets = SoftwareMLService.list_datasets(db)
        if sw_datasets:
            upload_id = sw_datasets[0].id
            bulk = SoftwareMLService.predict_all_from_upload(
                db=db,
                upload_id=upload_id,
                target_column="performance_band",
                use_llm_narrative=False,
            )
            for item in bulk.items:
                band = str(item.predicted_band)
                risk_pct = int(round(item.confidence * 100))
                if band == "Riskli":
                    risk_level = "High"
                    risk_score = max(60, risk_pct)
                    perf_score = min(50, max(15, round(50 - item.confidence * 35)))
                else:
                    risk_level = "Low"
                    risk_score = min(40, 100 - risk_pct)
                    perf_score = min(95, max(55, round(55 + item.confidence * 40)))

                top_driver = None
                if item.top_drivers:
                    top_driver = item.top_drivers[0].get("metric_name")

                sp = item.summary_payload
                employees.append(FlightRiskEmployee(
                    employee_code=sp.get("external_employee_code") or f"SW-{item.employee_id:03d}",
                    employee_name=sp.get("employee_name"),
                    department="Yazilim",
                    position=sp.get("position"),
                    team=sp.get("team"),
                    risk_level=risk_level,
                    risk_score=risk_score,
                    performance_score=perf_score,
                    confidence=item.confidence,
                    top_driver=top_driver,
                    predicted_band=band,
                ))
    except Exception:
        pass

    # Yüksek risk önce, sonra confidence'a göre sırala
    order = {"High": 0, "Medium": 1, "Low": 2}
    employees.sort(key=lambda e: (order.get(e.risk_level, 3), -e.risk_score))

    high = sum(1 for e in employees if e.risk_level == "High")
    medium = sum(1 for e in employees if e.risk_level == "Medium")
    low = sum(1 for e in employees if e.risk_level == "Low")

    return FlightRiskResponse(
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        employees=employees,
    )


@router.get('/ai-insights')
def get_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """
    ML flight-risk verisini Gemini ile yorumlar; KPI özeti + narratif + çalışan tablosu döner.
    """
    from app.services.ai_service import AIService

    # ── 1. ML verisini çek (flight-risk ile aynı mantık) ──────────────────
    all_emps: list[FlightRiskEmployee] = []

    try:
        from app.services.sales_ml_service import SalesMLService
        sales_datasets = SalesMLService.list_datasets(db)
        if sales_datasets:
            upload_id = sales_datasets[0].id
            sales_risk_map: dict[int, dict] = {}
            for target_col, weight in [
                ("Performance_Drop_Target", 1.0),
                ("Resignation_Target", 1.2),
                ("High_Risk_Target", 0.8),
            ]:
                try:
                    b = SalesMLService.predict_all_from_upload(
                        db=db, upload_id=upload_id,
                        target_column=target_col, use_llm_narrative=False,
                    )
                    for item in b.items:
                        eid = item.employee_id
                        band = str(item.predicted_band)
                        base_score = int(round(item.confidence * 100)) if band == "1" else int(round((1 - item.confidence) * 100))
                        weighted = int(base_score * weight) if band == "1" else 0
                        existing = sales_risk_map.get(eid, {})
                        if weighted > existing.get("weighted", 0):
                            sales_risk_map[eid] = {"item": item, "band": band, "weighted": weighted, "risk_score": base_score}
                        elif eid not in sales_risk_map:
                            sales_risk_map[eid] = {"item": item, "band": band, "weighted": 0, "risk_score": base_score}
                except Exception:
                    pass
            for eid, data in sales_risk_map.items():
                item = data["item"]
                band = data["band"]
                conf = item.confidence
                risk_level = "High" if data["weighted"] >= 60 else "Low"
                perf_score = min(50, max(15, round(50 - conf * 35))) if band == "1" else min(95, max(55, round(55 + conf * 40)))
                top_driver = item.top_drivers[0].get("metric_name") if item.top_drivers else None
                all_emps.append(FlightRiskEmployee(
                    employee_code=item.summary_payload.get("external_employee_code") or f"SA-{eid:03d}",
                    employee_name=item.summary_payload.get("employee_name"),
                    department="Satış",
                    position=item.summary_payload.get("position"),
                    team=item.summary_payload.get("team"),
                    risk_level=risk_level,
                    risk_score=data["weighted"] if risk_level == "High" else int(conf * 40),
                    performance_score=perf_score,
                    confidence=conf,
                    top_driver=top_driver,
                    predicted_band=band,
                ))
    except Exception:
        pass

    try:
        from app.services.software_ml_service import SoftwareMLService
        sw_datasets = SoftwareMLService.list_datasets(db)
        if sw_datasets:
            bulk = SoftwareMLService.predict_all_from_upload(
                db=db, upload_id=sw_datasets[0].id,
                target_column="performance_band", use_llm_narrative=False,
            )
            for item in bulk.items:
                band = str(item.predicted_band)
                conf = item.confidence
                risk_pct = int(round(conf * 100))
                if band == "Riskli":
                    risk_level, risk_score = "High", max(60, risk_pct)
                    perf_score = min(50, max(15, round(50 - conf * 35)))
                else:
                    risk_level, risk_score = "Low", min(40, 100 - risk_pct)
                    perf_score = min(95, max(55, round(55 + conf * 40)))
                sp = item.summary_payload
                top_driver = item.top_drivers[0].get("metric_name") if item.top_drivers else None
                all_emps.append(FlightRiskEmployee(
                    employee_code=sp.get("external_employee_code") or f"SE-{item.employee_id:03d}",
                    employee_name=sp.get("employee_name"),
                    department="Yazılım",
                    position=sp.get("position"),
                    team=sp.get("team"),
                    risk_level=risk_level,
                    risk_score=risk_score,
                    performance_score=perf_score,
                    confidence=conf,
                    top_driver=top_driver,
                    predicted_band=band,
                ))
    except Exception:
        pass

    # ── 2. Özet istatistikler ──────────────────────────────────────────────
    high = [e for e in all_emps if e.risk_level == "High"]
    low  = [e for e in all_emps if e.risk_level == "Low"]
    sales_emps = [e for e in all_emps if e.department == "Satış"]
    sw_emps    = [e for e in all_emps if e.department == "Yazılım"]

    avg_perf_all   = round(sum(e.performance_score for e in all_emps) / max(len(all_emps), 1), 1)
    avg_perf_sales = round(sum(e.performance_score for e in sales_emps) / max(len(sales_emps), 1), 1)
    avg_perf_sw    = round(sum(e.performance_score for e in sw_emps)    / max(len(sw_emps), 1),    1)

    # En riskli 10 çalışan (driver ile)
    top_risk = sorted(high, key=lambda e: -e.risk_score)[:10]

    kpis = [
        {"title": "Toplam Çalışan", "value": str(len(all_emps)), "trend": "ML Analizi", "trendColor": "text-blue-500", "comparison": "Her iki departman"},
        {"title": "Yüksek Riskli", "value": str(len(high)), "trend": "Dikkat", "trendColor": "text-red-500", "comparison": "Acil müdahale gerekli"},
        {"title": "Ort. Performans", "value": f"{avg_perf_all}/100", "trend": "Stabil" if avg_perf_all >= 60 else "Düşük", "trendColor": "text-emerald-600" if avg_perf_all >= 60 else "text-amber-500", "comparison": "ML tahmin skoru"},
        {"title": "Güvenli Çalışan", "value": str(len(low)), "trend": "İyi", "trendColor": "text-emerald-600", "comparison": "Düşük uçuş riski"},
    ]

    risk_data = [len(low), 0, len(high)]   # [düşük, orta, yüksek]

    employee_table = [
        {
            "code": e.employee_code,
            "name": e.employee_name or e.employee_code,
            "department": e.department,
            "team": e.team or "—",
            "position": e.position or "—",
            "risk_level": e.risk_level,
            "performance_score": e.performance_score,
            "top_driver": e.top_driver or "—",
        }
        for e in sorted(all_emps, key=lambda x: (-x.risk_score, -x.performance_score))
    ]

    # ── 3. Gemini yorum üret ───────────────────────────────────────────────
    narrative = None
    recommendations = []

    if AIService.GEMINI_API_KEY:
        high_list = "\n".join(
            f"- {e.employee_name or e.employee_code} ({e.department}, {e.team or '?'}, perf={e.performance_score}/100, driver: {e.top_driver or '?'})"
            for e in top_risk
        )
        prompt = f"""
Sen bir kurumsal performans analisti yapay zekasısın. Aşağıdaki ML tabanlı çalışan risk analizi sonuçlarını incele ve Türkçe, profesyonel bir yönetim raporu hazırla.

## Genel Tablo
- Toplam çalışan: {len(all_emps)} (Satış: {len(sales_emps)}, Yazılım: {len(sw_emps)})
- Yüksek riskli: {len(high)} çalışan (%{round(len(high)/max(len(all_emps),1)*100)})
- Güvenli: {len(low)} çalışan
- Ort. performans: {avg_perf_all}/100 (Satış: {avg_perf_sales}, Yazılım: {avg_perf_sw})

## En Riskli Çalışanlar (ML Tarafından Tespit)
{high_list if high_list else "Yüksek riskli çalışan tespit edilmedi."}

## Görev
Aşağıdaki 3 bölümü yaz:

### 1. GENEL DURUM DEĞERLENDİRMESİ (2-3 paragraf)
Organizasyonun genel sağlığını, risk dağılımını ve departman karşılaştırmasını yorumla.

### 2. KRİTİK BULGULAR (madde madde, en fazla 5 madde)
En önemli risk sinyallerini ve dikkat gerektiren örüntüleri listele.

### 3. YÖNETİCİYE AKSİYON ÖNERİLERİ (5 öneri, her biri kısa ve eyleme geçirilebilir)
Departman yöneticilerine somut, ölçülebilir adımlar öner.

Yanıtı bu 3 başlık altında yaz. Başlıkları ### ile işaretle. Türkçe, profesyonel ve özlü ol.
"""
        raw = AIService._generate_with_gemini(prompt, timeout_seconds=30)
        if raw:
            narrative = raw
            # Aksiyonları öneri kartları olarak da döndür
            lines = [l.strip() for l in raw.split('\n') if l.strip()]
            in_actions = False
            for line in lines:
                if 'AKSİYON' in line.upper() or 'ÖNERİ' in line.upper():
                    in_actions = True
                    continue
                if in_actions and (line.startswith('-') or (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
                    text = line.lstrip('-0123456789.) ').strip()
                    if text and len(recommendations) < 5:
                        recommendations.append({"title": text[:80], "description": "", "icon": "LightBulbIcon"})

    # Fallback öneriler (Gemini yoksa veya hata varsa)
    if not recommendations:
        if len(high) > 0:
            recommendations.append({"title": "Yüksek Riskli Çalışanlarla Görüşme", "description": f"{len(high)} çalışan ML modeli tarafından yüksek risk olarak işaretlendi. Bu hafta bire-bir görüşme planlayın.", "icon": "ExclamationCircleIcon"})
        if avg_perf_sw < 60:
            recommendations.append({"title": "Yazılım Ekibi Performans Desteği", "description": f"Yazılım departmanı ort. performansı {avg_perf_sw}/100. Teknik blokajları ve iş yükünü gözden geçirin.", "icon": "ArrowTrendingDownIcon"})
        if avg_perf_sales < 60:
            recommendations.append({"title": "Satış Ekibi Koçluk Programı", "description": f"Satış departmanı ort. performansı {avg_perf_sales}/100. Pipeline kalitesini ve takip disiplinini iyileştirin.", "icon": "ArrowTrendingDownIcon"})
        if not recommendations:
            recommendations.append({"title": "Genel Durum Stabil", "description": "Organizasyon genelinde dengeli bir performans seyri gözlemleniyor.", "icon": "LightBulbIcon"})

    return {
        "kpis": kpis,
        "riskData": risk_data,
        "recommendations": recommendations,
        "narrative": narrative,
        "employee_table": employee_table,
        "stats": {
            "total": len(all_emps),
            "high_risk": len(high),
            "low_risk": len(low),
            "avg_perf_all": avg_perf_all,
            "avg_perf_sales": avg_perf_sales,
            "avg_perf_sw": avg_perf_sw,
        },
        "gemini_used": narrative is not None,
    }


@router.get('/org-network', response_model=OnaResponse)
def get_org_network(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """
    FeedbackResponse verisinden departmanlar arası iletişim ağını hesaplar.
    Her etkileşim (sender → receiver) departman bazında gruplanır.
    """
    # 1. Tüm feedback response'ları sender/receiver departmanlarıyla çek
    rows = (
        db.query(
            FeedbackResponse.sender_id,
            FeedbackResponse.receiver_id,
        ).all()
    )

    # 2. sender/receiver → department_id eşlemesi
    employee_to_dept: dict[int, int] = {}
    dept_to_name: dict[int, str] = {}
    dept_to_emp_count: dict[int, int] = defaultdict(int)

    employees = db.query(Employee).all()
    for emp in employees:
        if emp.department_id:
            employee_to_dept[emp.id] = emp.department_id
            dept_to_emp_count[emp.department_id] += 1
        if emp.department and emp.department_id not in dept_to_name:
            dept_to_name[emp.department_id] = emp.department.name

    # 3. Departman çiftleri arasındaki etkileşim sayısını hesapla
    edge_counts: dict[tuple[int, int], int] = defaultdict(int)
    internal_counts: dict[int, int] = defaultdict(int)
    external_counts: dict[int, int] = defaultdict(int)
    total_interactions = 0

    for sender_id, receiver_id in rows:
        s_dept = employee_to_dept.get(sender_id)
        r_dept = employee_to_dept.get(receiver_id)
        if not s_dept or not r_dept:
            continue
        total_interactions += 1
        if s_dept == r_dept:
            internal_counts[s_dept] += 1
        else:
            # (küçük id, büyük id) → yönsüz kenar
            key = (min(s_dept, r_dept), max(s_dept, r_dept))
            edge_counts[key] += 1
            external_counts[s_dept] += 1
            external_counts[r_dept] += 1

    # 4. Departman node'larını oluştur
    all_dept_ids = set(dept_to_name.keys())
    nodes: list[OnaNode] = []
    for dept_id in sorted(all_dept_ids):
        ext = external_counts.get(dept_id, 0)
        intr = internal_counts.get(dept_id, 0)
        total_dept = ext + intr
        centrality = round(ext / total_dept, 3) if total_dept > 0 else 0.0
        is_silo = (centrality < 0.20) or (ext == 0)
        nodes.append(OnaNode(
            id=dept_id,
            name=dept_to_name.get(dept_id, f"Dept-{dept_id}"),
            employee_count=dept_to_emp_count.get(dept_id, 0),
            centrality=centrality,
            is_silo=is_silo,
            internal_count=intr,
            external_count=ext,
        ))

    # 5. Kenarları oluştur (gerçek veri)
    cross_total = sum(edge_counts.values())
    max_weight = max(edge_counts.values(), default=1)
    edges: list[OnaEdge] = []
    for (src, tgt), w in sorted(edge_counts.items(), key=lambda x: -x[1]):
        ratio = w / max_weight
        strength = "strong" if ratio >= 0.6 else ("medium" if ratio >= 0.3 else "weak")
        edges.append(OnaEdge(source_id=src, target_id=tgt, weight=w, strength=strength))

    data_source = "feedback"

    # 6. Fallback: gerçek çapraz-departman verisi yoksa KPI + yapısal yakınlık kullan
    if cross_total == 0 and len(nodes) >= 2:
        data_source = "inferred"

        # KPI kayıtlarından Ekip Katkı Skoru (EKS) ortalaması çek — işbirliği göstergesi
        from app.db.models.kpi import KPI, KPIRecord
        from sqlalchemy import func as sql_func

        # Her departman için ortalama EKS skoru (varsa)
        dept_eks: dict[int, float] = {}
        for dept_id in all_dept_ids:
            result = (
                db.query(sql_func.avg(KPIRecord.value))
                .join(KPI, KPI.id == KPIRecord.kpi_id)
                .join(Employee, Employee.id == KPIRecord.employee_id)
                .filter(
                    Employee.department_id == dept_id,
                    KPI.name.ilike("%Ekip Katki%"),
                )
                .scalar()
            )
            dept_eks[dept_id] = float(result) if result else 50.0

        # Tüm departman çiftleri için çapraz bağlantı oluştur
        dept_list = sorted(all_dept_ids)
        for i in range(len(dept_list)):
            for j in range(i + 1, len(dept_list)):
                a, b = dept_list[i], dept_list[j]
                # Bağlantı gücü = iki departmanın EKS ortalaması / 100
                avg_eks = (dept_eks.get(a, 50.0) + dept_eks.get(b, 50.0)) / 2
                weight = max(1, int(avg_eks * dept_to_emp_count.get(a, 10) / 100))
                strength = "strong" if avg_eks >= 65 else ("medium" if avg_eks >= 45 else "weak")
                edges.append(OnaEdge(source_id=a, target_id=b, weight=weight, strength=strength))
                # Centrality güncelle (inferred modunda)
                cent = round(avg_eks / 100, 3)
                nodes = [
                    OnaNode(
                        id=n.id, name=n.name, employee_count=n.employee_count,
                        centrality=cent, is_silo=False, external_count=weight,
                        internal_count=n.internal_count,
                    ) if n.id in (a, b) else n
                    for n in nodes
                ]

        cross_total = sum(e.weight for e in edges)

    # 7. Özet
    silo_names = [n.name for n in nodes if n.is_silo]
    most_central = max(nodes, key=lambda n: n.centrality, default=None)
    bridge_names = [
        f"{dept_to_name.get(e.source_id, '?')} → {dept_to_name.get(e.target_id, '?')}"
        for e in edges if e.strength in ("strong", "medium")
    ]

    return OnaResponse(
        nodes=nodes,
        edges=edges,
        summary=OnaSummary(
            total_interactions=total_interactions,
            cross_dept_interactions=cross_total,
            most_central_dept=most_central.name if most_central else None,
            silos=silo_names,
            bridges=bridge_names,
        ),
        data_source=data_source,
    )


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
