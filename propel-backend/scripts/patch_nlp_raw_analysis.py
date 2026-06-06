"""
Seeded FeedbackNLPAnalysis kayıtlarının raw_analysis alanını doldurur.
Bu alan: complaint_topics, praise_topics, theme_labels, entity_mentions,
          flight_risk_score, flight_risk_reasons, action_recommendation
"""

import sys
sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.db.models.nlp import FeedbackNLPAnalysis, RiskLevel
from app.db.models.feedback import FeedbackResponse

db = SessionLocal()

# ── Profile bazlı raw_analysis şablonları ────────────────────────────────────

RAW_ANALYSIS_BY_PROFILE = {
    "high": {
        "complaint_topics": [],
        "praise_topics": [
            "güçlü teknik liderlik", "yüksek test disiplini", "proaktif iletişim",
            "hızlı problem çözme", "ekip uyumu"
        ],
        "theme_labels": ["yüksek performans", "ekip katkısı", "teknik mükemmellik"],
        "entity_mentions": ["sprint planlama", "code review", "pull request kalitesi"],
        "flight_risk_score": 2.1,
        "flight_risk_reasons": [],
        "action_recommendation": "Mevcut motivasyonu koruyun, liderlik fırsatları sunun.",
        "quality_signal": {"is_low_quality": False, "quality_reasons": []},
        "reciprocity_signal": {"reciprocity_bias_suspected": False},
    },
    "medium": {
        "complaint_topics": ["inisiyatif eksikliği", "dokümantasyon gecikmesi"],
        "praise_topics": ["stabil performans", "ekip uyumu", "güvenilir teslimat"],
        "theme_labels": ["stabil performans", "gelişim fırsatı"],
        "entity_mentions": ["sprint süreci", "ekip iletişimi"],
        "flight_risk_score": 3.8,
        "flight_risk_reasons": [],
        "action_recommendation": "Gelişim planı yapın, mentorluk desteği sağlayın.",
        "quality_signal": {"is_low_quality": False, "quality_reasons": []},
        "reciprocity_signal": {"reciprocity_bias_suspected": False},
    },
    "medium_risk": {
        "complaint_topics": [
            "motivasyon dalgalanması", "stres yönetimi zayıf", "iletişim kalitesi düşük"
        ],
        "praise_topics": ["temel yetkinlikler mevcut", "takım çalışması"],
        "theme_labels": ["orta düzey risk", "stres sinyali", "destek ihtiyacı"],
        "entity_mentions": ["motivasyon trendi", "stres faktörü", "iş yükü"],
        "flight_risk_score": 5.5,
        "flight_risk_reasons": [
            "motivasyon düşüşü gözlemlendi",
            "yorgunluk belirtileri mevcut",
        ],
        "action_recommendation": "Birebir görüşme planlayın, iş yükünü gözden geçirin.",
        "quality_signal": {"is_low_quality": False, "quality_reasons": []},
        "reciprocity_signal": {"reciprocity_bias_suspected": False},
    },
    "atrisk": {
        "complaint_topics": [
            "tükenmişlik riski", "ayrılma sinyali", "bağlılık kaybı",
            "düşük motivasyon", "kopma davranışı"
        ],
        "praise_topics": [],
        "theme_labels": ["yüksek risk", "tükenmişlik", "ayrılma riski"],
        "entity_mentions": ["motivasyon kaybı", "psikolojik güvensizlik", "ayrılma niyeti"],
        "flight_risk_score": 8.2,
        "flight_risk_reasons": [
            "ayrılmayı düşündüğünü ima etti",
            "aidiyet hissi ciddi şekilde azalmış",
            "ekipten kopma sinyali net",
            "tükenmişlik belirtileri açık",
        ],
        "action_recommendation": "Acil görüşme yapın, tükenmişlik nedenlerini tespit edin ve aksiyon alın.",
        "quality_signal": {"is_low_quality": False, "quality_reasons": []},
        "reciprocity_signal": {"reciprocity_bias_suspected": False},
    },
}

# Yazılım profil haritası (emp_id → profile_key)
YAZILIM_PROFILES = {
    194: "high", 197: "high", 198: "medium", 199: "medium", 200: "medium",
    201: "high", 202: "high", 203: "atrisk", 204: "medium_risk", 205: "high",
    206: "medium", 207: "high", 208: "medium", 209: "atrisk", 210: "high",
    211: "medium", 212: "atrisk", 213: "medium_risk", 214: "medium", 215: "atrisk",
    216: "medium", 217: "atrisk", 218: "medium_risk", 219: "atrisk", 220: "medium_risk",
    221: "high", 222: "medium", 223: "high", 224: "medium_risk", 225: "medium", 226: "high",
}


def get_profile(emp_id, dept_id):
    from app.db.models.employee import Employee
    if emp_id in YAZILIM_PROFILES:
        return YAZILIM_PROFILES[emp_id]
    # Satış: yaklaşık profil ata
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        return "medium"
    pos = (emp.position or "").lower()
    if "manager" in pos or "lead" in pos:
        return "high"
    # Satış için basit hash tabanlı atama
    bucket = emp_id % 4
    if bucket == 0:
        return "atrisk"
    elif bucket == 1:
        return "medium_risk"
    elif bucket == 2:
        return "medium"
    else:
        return "high"


# ── Patch ─────────────────────────────────────────────────────────────────────

analyses = (
    db.query(FeedbackNLPAnalysis)
    .filter(FeedbackNLPAnalysis.model_provider == "synthetic_seed_360")
    .filter(FeedbackNLPAnalysis.raw_analysis.is_(None))
    .all()
)

print(f"Güncellenecek NLP analiz sayısı: {len(analyses)}")

batch_size = 200
updated = 0

for i, nlp in enumerate(analyses):
    profile_key = get_profile(nlp.employee_id, nlp.department_id)
    raw = dict(RAW_ANALYSIS_BY_PROFILE[profile_key])

    # Tema bilgisini ekle
    if nlp.theme:
        if nlp.theme not in raw["theme_labels"]:
            raw["theme_labels"] = [nlp.theme] + raw["theme_labels"][:2]

    nlp.raw_analysis = raw
    updated += 1

    if (i + 1) % batch_size == 0:
        db.commit()
        print(f"  {i + 1}/{len(analyses)} güncellendi...")

db.commit()
print(f"\n✅ Tamamlandı: {updated} NLP analiz kaydı raw_analysis ile güncellendi.")

# Doğrulama
sample = db.query(FeedbackNLPAnalysis).filter(
    FeedbackNLPAnalysis.model_provider == "synthetic_seed_360"
).limit(3).all()

for s in sample:
    ra = s.raw_analysis or {}
    print(f"  emp={s.employee_id} complaint={ra.get('complaint_topics',[])} flight_score={ra.get('flight_risk_score')}")
