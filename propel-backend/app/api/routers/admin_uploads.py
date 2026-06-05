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


# threshold_status → numeric score mapping (ML explain output değerleri)
_THRESHOLD_SCORE: dict[str, int] = {
    "Guclu seviyede":              92,
    "Optimal aralikta":            85,
    "Optimal araligin ustunde":    88,
    "Normal seviyede":             72,
    "Izleme seviyesinde":          55,
    "Optimal araligin altinda":    42,
    "Risk esiginin altinda":       25,
    "Risk esiginin ustunde":       25,
    "Veri yorumu icin sayisal deger yok": 60,
}


def _perf_from_drivers(top_drivers: list[dict], fallback_band: str, fallback_conf: float) -> int:
    """ML top_drivers'dan KPI eşik durumlarına göre performans skoru hesapla."""
    seen: set[str] = set()
    total_w = 0.0
    total_s = 0.0
    for d in (top_drivers or []):
        feat = d.get("feature", "")
        # Türetilmiş zaman özelliklerini atla (sadece anlık değer kullan)
        if any(feat.endswith(s) for s in ("_lag_1", "_rolling_4", "_trend_4")):
            continue
        key = d.get("metric_code") or feat
        if key in seen:
            continue
        seen.add(key)
        status = d.get("threshold_status", "Normal seviyede")
        score = _THRESHOLD_SCORE.get(status, 60)
        w = float(d.get("importance", 1.0))
        total_s += score * w
        total_w += w

    if total_w == 0:
        # Fallback: eski confidence formülü
        if str(fallback_band) in ("0", "Iyi", "İyi", "high"):
            return min(95, max(55, round(55 + fallback_conf * 40)))
        return min(50, max(15, round(50 - fallback_conf * 35)))

    return max(10, min(100, round(total_s / total_w)))


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

                perf_score = _perf_from_drivers(item.top_drivers, band, item.confidence)

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
                else:
                    risk_level = "Low"
                    risk_score = min(40, 100 - risk_pct)
                perf_score = _perf_from_drivers(item.top_drivers, band, item.confidence)

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
    Satış + Yazılım departmanı toplu tara (4 hedef) sonuçlarını grafikler + LLM narratifi ile döndürür.
    """
    from app.services.ai_service import AIService

    # ── Risk hedef tanımları ──────────────────────────────────────────────
    RISK_DEFINITIONS = [
        {
            "key": "perf_drop",
            "target": "Performance_Drop_Target",
            "label": "Performans Düşüşü",
            "color": "rose",
            "description": "Çalışanın son dönemlere göre performansında belirgin bir gerileme yaşanıp yaşanmadığını tahmin eder.",
            "boundary": "Risk eşiği: Model %50+ olasılık tahmin ettiğinde 'riskli' kabul edilir. Beklenen oran: toplam çalışanın %15-35'i.",
            "signals": ["Görev tamamlama oranı düşüşü", "Hedef gerçekleşme gerilemesi", "Motivasyon skoru azalması"],
        },
        {
            "key": "burnout",
            "target": "Burnout_Target",
            "label": "Tükenmişlik",
            "color": "amber",
            "description": "Yüksek iş yükü, düşük motivasyon ve uzun süreli stres kombinasyonundan kaynaklanan tükenme riskini tahmin eder.",
            "boundary": "Risk eşiği: İş yükü endeksi >1.2 ve motivasyon skoru <3.0 kombinasyonu kritik sinyaldir. Beklenen oran: %20-40.",
            "signals": ["İş yükü endeksi yüksekliği", "Motivasyon düşüşü trendi", "Mesai saati artışı"],
        },
        {
            "key": "resignation",
            "target": "Resignation_Target",
            "label": "İstifa Riski",
            "color": "orange",
            "description": "Çalışanın yakın vadede kurumu terk etme olasılığını tahmin eder. Motivasyon, performans ve çevre faktörlerini birleştirir.",
            "boundary": "Risk eşiği: Model %50+ olasılık tahmin ettiğinde izleme listesine alınır. Beklenen oran: %15-30.",
            "signals": ["Uzun süreli motivasyon düşüklüğü", "Hedef altı performans", "CRM/araç kullanım azalması"],
        },
        {
            "key": "high_risk",
            "target": "High_Risk_Target",
            "label": "Yüksek Risk",
            "color": "purple",
            "description": "Performans düşüşü + tükenmişlik + istifa riskinin birleşik bileşik skoru. Birden fazla risk sinyali aynı anda aktif olan çalışanları tespit eder.",
            "boundary": "Risk eşiği: En az 2 hedefte aynı anda yüksek risk → bileşik yüksek risk. Beklenen oran: %10-20.",
            "signals": ["Çoklu risk sinyali kombinasyonu", "Uzun süreli düşük performans + yüksek iş yükü", "Ekip dinamiklerinde bozulma"],
        },
    ]

    # ── 1. Her iki departman için predict_all_targets çağır ──────────────
    sales_bulk = None
    sw_bulk    = None

    try:
        from app.services.sales_ml_service import SalesMLService
        sales_datasets = SalesMLService.list_datasets(db)
        if sales_datasets:
            sales_bulk = SalesMLService.predict_all_targets(
                db=db, upload_id=sales_datasets[0].id, use_llm_narrative=False
            )
    except Exception:
        pass

    try:
        from app.services.software_ml_service import SoftwareMLService
        sw_datasets = SoftwareMLService.list_datasets(db)
        if sw_datasets:
            sw_bulk = SoftwareMLService.predict_all_targets(
                db=db, upload_id=sw_datasets[0].id, use_llm_narrative=False
            )
    except Exception:
        pass

    # ── 2. Çalışan tablosu — 4 hedef bazlı ──────────────────────────────
    def _risk_pct(t: Any) -> int:
        if t is None:
            return 0
        band = t.predicted_band if hasattr(t, "predicted_band") else t.get("predicted_band", "0")
        conf = t.confidence if hasattr(t, "confidence") else t.get("confidence", 0)
        return round(float(conf if str(band) == "1" else 1 - conf) * 100)

    def _composite(emp: Any) -> int:
        pd_ = _risk_pct(emp.perf_drop)   if hasattr(emp, "perf_drop")   else 0
        bk_ = _risk_pct(emp.burnout)     if hasattr(emp, "burnout")     else 0
        rs_ = _risk_pct(emp.resignation) if hasattr(emp, "resignation") else 0
        hr_ = _risk_pct(emp.high_risk)   if hasattr(emp, "high_risk")   else 0
        return round(pd_ * 0.35 + rs_ * 0.30 + hr_ * 0.25 + bk_ * 0.10)

    sales_rows = [
        {
            "code":       e.external_employee_code or f"SA-{e.employee_id:03d}",
            "name":       e.employee_name or e.external_employee_code or f"SA-{e.employee_id:03d}",
            "department": "Satış",
            "team":       e.team or "—",
            "perf_drop":  _risk_pct(e.perf_drop),
            "burnout":    _risk_pct(e.burnout),
            "resignation":_risk_pct(e.resignation),
            "high_risk":  _risk_pct(e.high_risk),
            "composite":  _composite(e),
        }
        for e in (sales_bulk.employees if sales_bulk else [])
    ]

    sw_rows = [
        {
            "code":       e.external_employee_code or f"SE-{e.employee_id:03d}",
            "name":       e.employee_name or e.external_employee_code or f"SE-{e.employee_id:03d}",
            "department": "Yazılım",
            "team":       e.team or "—",
            "perf_drop":  _risk_pct(e.perf_drop),
            "burnout":    _risk_pct(e.burnout),
            "resignation":_risk_pct(e.resignation),
            "high_risk":  _risk_pct(e.high_risk),
            "composite":  _composite(e),
        }
        for e in (sw_bulk.employees if sw_bulk else [])
    ]

    all_rows = sorted(sales_rows + sw_rows, key=lambda r: -r["composite"])

    # ── 3. Grafik verileri — hedef bazlı risk dağılımı ───────────────────
    def _dist(rows: list[dict], key: str, thr: int = 50) -> dict:
        risky = sum(1 for r in rows if r.get(key, 0) >= thr)
        safe  = len(rows) - risky
        return {"risky": risky, "safe": safe, "total": len(rows),
                "risky_pct": round(risky / max(len(rows), 1) * 100)}

    chart_data = {
        "sales": {
            "total": len(sales_rows),
            "perf_drop":   _dist(sales_rows, "perf_drop"),
            "burnout":     _dist(sales_rows, "burnout"),
            "resignation": _dist(sales_rows, "resignation"),
            "high_risk":   _dist(sales_rows, "high_risk"),
        },
        "software": {
            "total": len(sw_rows),
            "perf_drop":   _dist(sw_rows, "perf_drop"),
            "burnout":     _dist(sw_rows, "burnout"),
            "resignation": _dist(sw_rows, "resignation"),
            "high_risk":   _dist(sw_rows, "high_risk"),
        },
    }

    # ── 4. Özet KPI kartları ─────────────────────────────────────────────
    all_emps_count = len(all_rows)
    high_composite = sum(1 for r in all_rows if r["composite"] >= 50)
    avg_composite  = round(sum(r["composite"] for r in all_rows) / max(all_emps_count, 1), 1)

    kpis = [
        {"title": "Toplam Çalışan",   "value": str(all_emps_count), "trend": "ML Analizi",     "trendColor": "text-blue-500",    "comparison": "Her iki departman"},
        {"title": "Yüksek Risk",       "value": str(high_composite), "trend": "Dikkat",          "trendColor": "text-red-500",     "comparison": "Bileşik risk ≥ %50"},
        {"title": "Ort. Genel Risk",   "value": f"%{avg_composite}", "trend": "Bileşik Skor",    "trendColor": "text-amber-600",   "comparison": "4 hedef ağırlıklı ort."},
        {"title": "Güvenli Çalışan",   "value": str(all_emps_count - high_composite), "trend": "İyi", "trendColor": "text-emerald-600", "comparison": "Bileşik risk < %50"},
    ]

    risk_data = [all_emps_count - high_composite, 0, high_composite]

    # En riskli 10 çalışan
    top_risk = all_rows[:10]

    # Eski all_emps (flight-risk uyumlu) — diğer kod için
    all_emps: list[FlightRiskEmployee] = []
    sales_emps = sales_rows
    sw_emps    = sw_rows
    avg_perf_all   = avg_composite
    avg_perf_sales = round(sum(r["composite"] for r in sales_rows) / max(len(sales_rows), 1), 1)
    avg_perf_sw    = round(sum(r["composite"] for r in sw_rows)    / max(len(sw_rows), 1),    1)

    employee_table = all_rows

    # ── 3. Gemini yorum üret ───────────────────────────────────────────────
    narrative = None
    recommendations = []

    if AIService.GEMINI_API_KEY:
        high_list = "\n".join(
            f"- {r['name']} ({r['department']}/{r['team']}) → PD:{r['perf_drop']}% TK:{r['burnout']}% İR:{r['resignation']}% YR:{r['high_risk']}% | Bileşik:{r['composite']}%"
            for r in top_risk
        )
        s = chart_data["sales"]
        w = chart_data["software"]
        prompt = f"""
Sen bir kurumsal performans analisti yapay zekasısın. 4 ayrı ML modeli (Performans Düşüşü, Tükenmişlik, İstifa Riski, Yüksek Risk) sonuçlarını Türkçe profesyonel bir rapor olarak yorumla.

## Departman Özeti
Satış ({s['total']} kişi): PD:{s['perf_drop']['risky_pct']}% | TK:{s['burnout']['risky_pct']}% | İR:{s['resignation']['risky_pct']}% | YR:{s['high_risk']['risky_pct']}%
Yazılım ({w['total']} kişi): PD:{w['perf_drop']['risky_pct']}% | TK:{w['burnout']['risky_pct']}% | İR:{w['resignation']['risky_pct']}% | YR:{w['high_risk']['risky_pct']}%
Toplam: {all_emps_count} çalışan | Bileşik yüksek risk: {high_composite} kişi (%{round(high_composite/max(all_emps_count,1)*100)}) | Ort. bileşik risk: %{avg_composite}

## En Riskli 10 Çalışan
{high_list or "Yüksek riskli çalışan tespit edilmedi."}

## Görev — 3 bölüm yaz:
### 1. GENEL DURUM DEĞERLENDİRMESİ
Hangi departmanda hangi risk tipi öne çıkıyor? Organizasyonun genel sağlığını yorumla.

### 2. KRİTİK BULGULAR (en fazla 5 madde)
4 risk hedefi açısından en önemli örüntüler neler?

### 3. AKSİYON ÖNERİLERİ (5 öneri, somut ve kısa)
Risk tipine özgü, departman yöneticisine eyleme geçirilebilir adımlar.

Türkçe, profesyonel, özlü ol. ### başlıkları kullan.
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
        if high_composite > 0:
            recommendations.append({"title": "Yüksek Riskli Çalışanlarla Görüşme", "description": f"{high_composite} çalışan bileşik risk skoru ≥%50. Bu hafta bire-bir görüşme planlayın.", "icon": "ExclamationCircleIcon"})
        s_burn = chart_data["sales"]["burnout"]["risky_pct"]
        w_burn = chart_data["software"]["burnout"]["risky_pct"]
        if s_burn > 30:
            recommendations.append({"title": "Satış Ekibi Tükenmişlik Önlemi", "description": f"Satış ekibinin %{s_burn}'i tükenmişlik riskinde. İş yükü dengelemesi yapın.", "icon": "ArrowTrendingDownIcon"})
        if w_burn > 30:
            recommendations.append({"title": "Yazılım Ekibi İş Yükü Denetimi", "description": f"Yazılım ekibinin %{w_burn}'i tükenmişlik riskinde. Sprint kapasitesini gözden geçirin.", "icon": "ArrowTrendingDownIcon"})
        if not recommendations:
            recommendations.append({"title": "Genel Durum Stabil", "description": "Organizasyon genelinde dengeli bir risk seyri gözlemleniyor.", "icon": "LightBulbIcon"})

    return {
        "kpis": kpis,
        "riskData": risk_data,
        "recommendations": recommendations,
        "narrative": narrative,
        "employee_table": employee_table,
        "chart_data": chart_data,
        "risk_definitions": RISK_DEFINITIONS,
        "stats": {
            "total": all_emps_count,
            "high_risk": high_composite,
            "low_risk": all_emps_count - high_composite,
            "avg_composite": avg_composite,
            "avg_sales": avg_perf_sales,
            "avg_sw": avg_perf_sw,
            "sales_total": len(sales_rows),
            "sw_total": len(sw_rows),
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
