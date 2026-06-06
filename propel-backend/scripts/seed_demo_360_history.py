from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackDirection, FeedbackQuestion, FeedbackResponse
from app.db.models.nlp import FeedbackNLPAnalysis, NLPPeriodType
from app.db.models.rag import FeedbackMemoryChunk
from app.db.models.user import UserRole
from app.db.session import SessionLocal
from app.services.ai_service import AIService
from app.services.feedback_service import FeedbackService
from app.services.nlp_service import NLPService
from app.services.rag_service import RAGService


MODEL_PROVIDER = "synthetic_seed_360_history"
MODEL_NAME = "demo-360-history-v1"
DEFAULT_WEEKS = 12
DEFAULT_FEEDBACKS_PER_WEEK = 3


@dataclass(frozen=True)
class FeedbackPlan:
    sender: Employee
    receiver: Employee
    direction: FeedbackDirection
    signal: str
    topic: str
    feedback_date: datetime
    sequence: int


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    for source, target in {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
        "İ": "i",
        "Ä±": "i",
        "ÄŸ": "g",
        "Ã¼": "u",
        "ÅŸ": "s",
        "Ã¶": "o",
        "Ã§": "c",
        "Ä°": "i",
    }.items():
        text = text.replace(source, target)
    return text


def employee_label(employee: Employee) -> str:
    full_name = str(getattr(employee.user, "full_name", "") or "").strip() if employee.user else ""
    return full_name or employee.external_employee_code or f"Calisan #{employee.id}"


def department_key(department: Department) -> str:
    normalized = normalize_text(department.name)
    if "satis" in normalized or "sales" in normalized or "sat" in normalized:
        return "sales"
    if "yazilim" in normalized or "software" in normalized or "yaz" in normalized:
        return "software"
    return "general"


def get_target_departments(db: Session, target: str) -> list[Department]:
    departments = db.query(Department).order_by(Department.id.asc()).all()
    selected = []
    for department in departments:
        key = department_key(department)
        if target == "all" and key in {"software", "sales"}:
            selected.append(department)
        elif target == key:
            selected.append(department)
    if not selected:
        raise RuntimeError(f"Seed icin departman bulunamadi: {target}")
    return selected


def get_department_employees(db: Session, department_id: int) -> list[Employee]:
    employees = (
        db.query(Employee)
        .join(Employee.user)
        .filter(Employee.department_id == department_id)
        .filter(Employee.user.has(role=UserRole.employee) | Employee.user.has(role=UserRole.department_manager))
        .order_by(Employee.team.asc(), Employee.id.asc())
        .all()
    )
    if len(employees) < 4:
        raise RuntimeError("3 aylik 360 seed icin departmanda yeterli calisan yok.")
    return employees


def clear_existing_synthetic_rows(db: Session) -> int:
    analyses = (
        db.query(FeedbackNLPAnalysis)
        .filter(FeedbackNLPAnalysis.model_provider == MODEL_PROVIDER)
        .all()
    )
    response_ids = [analysis.weekly_feedback_id for analysis in analyses if analysis.weekly_feedback_id]
    deleted = len(response_ids)

    if response_ids:
        db.query(FeedbackMemoryChunk).filter(
            FeedbackMemoryChunk.weekly_feedback_id.in_(response_ids)
        ).delete(synchronize_session=False)

    for analysis in analyses:
        db.delete(analysis)
    db.flush()

    if response_ids:
        db.query(FeedbackResponse).filter(
            FeedbackResponse.id.in_(response_ids)
        ).delete(synchronize_session=False)

    db.commit()
    return deleted


def question_text(dept_key: str, direction: FeedbackDirection, topic: str) -> str:
    if dept_key == "sales":
        domain = {
            "delivery": "musteri takibi ve satis hedeflerine ilerleme",
            "quality": "CRM disiplini, teklif kalitesi ve sikayet yonetimi",
            "collaboration": "bolge ici is birligi ve ekip destegi",
            "leadership": "hedef netligi, koçluk ve baskiyi dengeleme",
            "growth": "gelisim katilimi, pipeline okuma ve mentorluk",
            "risk": "quota baskisi, is yuku ve ayrilma sinyalleri",
        }[topic]
    else:
        domain = {
            "delivery": "sprint teslimi, blokaj yonetimi ve is takibi",
            "quality": "kod kalitesi, test kapsami ve teknik borc",
            "collaboration": "ekip ici iletisim, destek alma/verme ve psikolojik guven",
            "leadership": "netlik, mentorluk ve karar alma destegi",
            "growth": "ogrenme, sahiplenme ve teknik gelisim",
            "risk": "is yuku, motivasyon ve ayrilma sinyalleri",
        }[topic]

    if direction == FeedbackDirection.manager_to_employee:
        return f"Bu hafta calisanin {domain} davranislarini somut ornekle nasil degerlendirirsiniz?"
    if direction == FeedbackDirection.employee_to_manager:
        return f"Bu hafta yoneticinin {domain} konusunda size etkisini somut ornekle nasil degerlendirirsiniz?"
    return f"Bu hafta birlikte calisirken bu kisinin {domain} tarafinda hangi somut sinyallerini gozlemlediniz?"


def ensure_question(
    db: Session,
    *,
    department_id: int,
    dept_key: str,
    week_number: int,
    direction: FeedbackDirection,
    topic: str,
) -> FeedbackQuestion:
    category = f"Demo 360 {topic}"
    question = (
        db.query(FeedbackQuestion)
        .filter(
            FeedbackQuestion.department_id == department_id,
            FeedbackQuestion.week_number == week_number,
            FeedbackQuestion.direction == direction,
            FeedbackQuestion.category == category,
        )
        .order_by(FeedbackQuestion.id.desc())
        .first()
    )
    if question:
        return question

    question = FeedbackQuestion(
        department_id=department_id,
        week_number=week_number,
        direction=direction,
        question_text=question_text(dept_key, direction, topic),
        category=category,
        is_ai_generated=False,
    )
    db.add(question)
    db.flush()
    return question


def is_manager(employee: Employee, dept_key: str) -> bool:
    role = getattr(employee.user, "role", None) if employee.user else None
    if role == UserRole.department_manager:
        return True
    team = normalize_text(employee.team)
    return ("yonetim" in team) if dept_key == "software" else ("genel" in team)


def direction_for(sender: Employee, receiver: Employee, dept_key: str) -> FeedbackDirection:
    sender_manager = is_manager(sender, dept_key)
    receiver_manager = is_manager(receiver, dept_key)
    if sender_manager and not receiver_manager:
        return FeedbackDirection.manager_to_employee
    if not sender_manager and receiver_manager:
        return FeedbackDirection.employee_to_manager
    return FeedbackDirection.peer_to_peer


def pick_sender(candidates: Iterable[Employee], receiver: Employee, offset: int) -> Employee | None:
    ordered = [employee for employee in candidates if employee.id != receiver.id]
    if not ordered:
        return None
    ordered = sorted(ordered, key=lambda employee: (employee.team or "", employee.external_employee_code or "", employee.id))
    return ordered[offset % len(ordered)]


def signal_for(receiver: Employee, week_index: int, sequence: int, dept_key: str) -> str:
    team = normalize_text(receiver.team)
    if dept_key == "sales":
        if "dogu" in team or "guneydogu" in team:
            pattern = ["risk", "development", "risk", "positive", "development", "risk"]
        elif "karadeniz" in team or "akdeniz" in team:
            pattern = ["development", "positive", "risk", "development", "positive", "development"]
        elif "genel" in team:
            pattern = ["development", "positive", "positive", "development", "risk", "positive"]
        else:
            pattern = ["positive", "development", "positive", "strong_positive", "development", "positive"]
    else:
        if "qa" in team:
            pattern = ["development", "risk", "positive", "development", "risk", "positive"]
        elif "backend" in team:
            pattern = ["positive", "development", "risk", "development", "positive", "development"]
        elif "devops" in team:
            pattern = ["positive", "risk", "development", "positive", "development", "risk"]
        elif "yonetim" in team:
            pattern = ["development", "positive", "development", "risk", "positive", "development"]
        else:
            pattern = ["positive", "development", "positive", "strong_positive", "development", "risk"]
    return pattern[(week_index + sequence) % len(pattern)]


def topics_for_week(week_index: int) -> list[str]:
    topic_rotation = [
        ["delivery", "collaboration", "quality"],
        ["risk", "leadership", "growth"],
        ["quality", "delivery", "collaboration"],
        ["growth", "risk", "leadership"],
    ]
    return topic_rotation[week_index % len(topic_rotation)]


def scores_for_signal(signal: str, topic: str) -> tuple[int, int, int, int]:
    if signal == "risk":
        if topic in {"risk", "leadership"}:
            return 2, 2, 2, 3
        return 3, 2, 2, 3
    if signal == "development":
        return 3, 3, 3, 4 if topic in {"quality", "growth"} else 3
    if signal == "strong_positive":
        return 5, 5, 4, 5
    return 4, 4, 4, 4


def context_for(dept_key: str, team: str | None, topic: str) -> str:
    normalized = normalize_text(team)
    if dept_key == "sales":
        base = {
            "marmara": "kurumsal musteri ziyaretleri ve teklif kapanislari",
            "ege": "yeni musteri kazanimi ve CRM takipleri",
            "karadeniz": "pipeline sagligi ve satis dongusu suresi",
            "akdeniz": "musteri memnuniyeti ve sikayet kapatma",
            "dogu": "quota baskisi ve saha gorusmeleri",
            "guneydogu": "yogun aktivite, bolge destegi ve musteri iliskisi",
            "ic": "orta bant hesap yonetimi ve ekip koordinasyonu",
            "genel": "hedef yonetimi ve departman koordinasyonu",
        }
        for key, value in base.items():
            if key in normalized:
                return value
        return "satis sureci ve musteri iliskileri"

    base = {
        "backend": "API entegrasyonu, code review ve servis stabilitesi",
        "frontend": "arayuz teslimi, tasarim uyumu ve kullanici deneyimi",
        "qa": "test senaryolari, regresyon takibi ve hata geri donusleri",
        "devops": "deploy, ortam stabilitesi ve operasyonel destek",
        "yonetim": "onceliklendirme, mentorluk ve ekipler arasi koordinasyon",
    }
    for key, value in base.items():
        if key in normalized:
            return value
    return "sprint akisi ve ekip koordinasyonu"


def personal_patterns(employee: Employee, dept_key: str) -> dict[str, list[str]]:
    backend_profiles = [
        {
            "strengths": ["code review sahiplenmesi", "api entegrasyon takibi", "net durum guncellemesi"],
            "complaints": ["api bagimliligi gec bildirme", "dokumantasyon eksigi", "blokaj eskalasyonu gecikmesi"],
            "themes": ["code review", "api entegrasyonu", "sprint planlama"],
        },
        {
            "strengths": ["veritabani sorgu optimizasyonu", "servis stabilitesi takibi", "log analizi disiplini"],
            "complaints": ["endpoint performans dalgalanmasi", "migration dokumani eksigi", "hata logu gec analizi"],
            "themes": ["performans optimizasyonu", "veritabani migration", "observability"],
        },
        {
            "strengths": ["entegrasyon test sahiplenmesi", "domain model netligi", "api sozlesmesi koruma"],
            "complaints": ["api sozlesmesi degisikligini gec duyurma", "entegrasyon testinde acik", "domain kararlarini gec dokumante etme"],
            "themes": ["api sozlesmesi", "entegrasyon testi", "domain modelleme"],
        },
    ]
    qa_profiles = [
        {
            "strengths": ["test otomasyonu disiplini", "detaylara dikkat", "hata kok neden analizi"],
            "complaints": ["test kapsaminda acik", "regresyon senaryosu gecikmesi", "kabul kriteri belirsizligi"],
            "themes": ["test otomasyonu", "regresyon takibi", "kalite kontrol"],
        },
        {
            "strengths": ["edge case yakalama", "hata raporu netligi", "release oncesi risk okuma"],
            "complaints": ["edge case dokumani eksigi", "bug onceligi belirsizligi", "test verisi hazirligi gecikmesi"],
            "themes": ["edge case analizi", "bug onceliklendirme", "release kalite kapisi"],
        },
    ]
    devops_profiles = [
        {
            "strengths": ["deploy sorumlulugu", "ortam stabilitesi takibi", "kriz aninda sakin koordinasyon"],
            "complaints": ["deploy sonrasi takip eksigi", "alarm onceligi belirsizligi", "operasyonel el degistirme gecikmesi"],
            "themes": ["deploy stabilitesi", "monitoring", "operasyonel destek"],
        },
        {
            "strengths": ["ci cd pipeline iyilestirme", "incident koordinasyonu", "kapasite planlama dikkati"],
            "complaints": ["pipeline kirilmasini gec bildirme", "incident postmortem eksigi", "kapasite uyarilarini gec eskale etme"],
            "themes": ["ci cd pipeline", "incident yonetimi", "kapasite planlama"],
        },
    ]
    frontend_profiles = [
        {
            "strengths": ["arayuz detay kalitesi", "tasarim uyumu", "kullanici akisi sahiplenmesi"],
            "complaints": ["arayuz kabul kriteri belirsizligi", "backend bagimliligi gec bildirme", "tasarim revizyonu gecikmesi"],
            "themes": ["arayuz teslimi", "kullanici deneyimi", "tasarim uyumu"],
        },
        {
            "strengths": ["component mimarisi sahiplenmesi", "state yonetimi netligi", "yeniden kullanilabilir UI disiplini"],
            "complaints": ["component parcalama gecikmesi", "state senkronizasyon hatasi", "props contract belirsizligi"],
            "themes": ["component mimarisi", "state yonetimi", "tasarim sistemi"],
        },
        {
            "strengths": ["erisilebilirlik farkindaligi", "form validasyon titizligi", "kullanici hata mesajlarini iyilestirme"],
            "complaints": ["mobil kirilim testi eksigi", "erisilebilirlik kontrolu gecikmesi", "form edge case kacagi"],
            "themes": ["erisilebilirlik", "mobil uyumluluk", "form deneyimi"],
        },
        {
            "strengths": ["performans optimizasyonu", "bundle analizi", "sayfa gecis akiciligi"],
            "complaints": ["render performansi dalgalanmasi", "lazy loading eksigi", "grafik bileseni yuklenme gecikmesi"],
            "themes": ["frontend performansi", "bundle optimizasyonu", "grafik render"],
        },
        {
            "strengths": ["backend kontrat takibi", "api hata durumlarini iyi ele alma", "entegrasyon test destegi"],
            "complaints": ["api hata state eksigi", "loading state tutarsizligi", "backend kontrat degisikligini gec yakalama"],
            "themes": ["api entegrasyonu", "hata state yonetimi", "loading deneyimi"],
        },
    ]
    leadership_profiles = [
        {
            "strengths": ["bilgi paylasimi", "mentorluk katkisi", "ekip koordinasyonu"],
            "complaints": ["toplanti yogunlugu", "oncelik degisikliklerinde zorlanma", "karar gerekcesi eksigi"],
            "themes": ["mentorluk", "ekip koordinasyonu", "karar netligi"],
        },
        {
            "strengths": ["roadmap netligi", "paydas iletisim becerisi", "riskleri erken gorunur kilma"],
            "complaints": ["sprint hedefi degisikligi", "paydas beklentisi belirsizligi", "karar zamanlamasi gecikmesi"],
            "themes": ["roadmap yonetimi", "paydas iletisimi", "risk yonetimi"],
        },
    ]
    sales_profiles = [
        {
            "strengths": ["musteri takip disiplini", "teklif kapatma odagi", "net sonraki adim takibi"],
            "complaints": ["musteri itirazlarini gec kapatma", "teklif revizyonu gecikmesi", "pipeline yaslanmasi"],
            "themes": ["musteri takip", "pipeline sagligi", "teklif yonetimi"],
        },
        {
            "strengths": ["crm kayit kalitesi", "bolge raporlama disiplini", "veriye dayali takip"],
            "complaints": ["crm guncelleme gecikmesi", "aktivite notu eksigi", "firsat asamasi belirsizligi"],
            "themes": ["crm disiplini", "aktivite takibi", "bolge raporlama"],
        },
        {
            "strengths": ["sikayet kapatma hizi", "musteri memnuniyeti odagi", "kriz iletisim becerisi"],
            "complaints": ["sikayet eskalasyonu gecikmesi", "musteri beklentisi netlestirme eksigi", "servis ekipleriyle kopukluk"],
            "themes": ["sikayet yonetimi", "musteri memnuniyeti", "servis koordinasyonu"],
        },
        {
            "strengths": ["quota yonetimi", "saha ziyareti planlama", "yeni musteri kazanimi"],
            "complaints": ["quota baskisi", "saha notu gecikmesi", "yeni lead takip eksigi"],
            "themes": ["quota yonetimi", "saha ziyareti", "lead takibi"],
        },
        {
            "strengths": ["ekip destegi", "mentorluk katkisi", "bolge koordinasyonu"],
            "complaints": ["destek talebini gec acma", "oncelik degisikliklerinde zorlanma", "yonetici check-in ihtiyaci"],
            "themes": ["ekip destegi", "mentorluk", "bolge koordinasyonu"],
        },
    ]
    team = normalize_text(employee.team)
    position = normalize_text(employee.position)
    if dept_key == "software":
        if "qa" in team or "qa" in position:
            return qa_profiles[employee.id % len(qa_profiles)]
        if "devops" in team or "devops" in position:
            return devops_profiles[employee.id % len(devops_profiles)]
        if "frontend" in team or "frontend" in position:
            return frontend_profiles[employee.id % len(frontend_profiles)]
        if "yonetim" in team or "manager" in position or "lead" in position:
            return leadership_profiles[employee.id % len(leadership_profiles)]
        if "backend" in team or "backend" in position:
            return backend_profiles[employee.id % len(backend_profiles)]
        fallback_profiles = backend_profiles + qa_profiles + devops_profiles + frontend_profiles + leadership_profiles
        return fallback_profiles[employee.id % len(fallback_profiles)]

    if "marmara" in team or "ege" in team:
        return sales_profiles[0]
    if "karadeniz" in team or "ic" in team:
        return sales_profiles[1]
    if "akdeniz" in team:
        return sales_profiles[2]
    if "dogu" in team or "guneydogu" in team:
        return sales_profiles[3]
    if "genel" in team or "manager" in position or "lead" in position:
        return sales_profiles[4]
    return sales_profiles[employee.id % len(sales_profiles)]


def individual_focus(employee: Employee, dept_key: str) -> dict[str, str]:
    software_focuses = [
        {
            "strength": "pull request aciklama kalitesi",
            "complaint": "acceptance criteria sorularini gec netlestirme",
            "theme": "pr dokumantasyonu",
        },
        {
            "strength": "karmasik buglari sade anlatma",
            "complaint": "edge case senaryolarini sprint sonuna birakma",
            "theme": "edge case sahiplenme",
        },
        {
            "strength": "cross-team bagimlilik takibi",
            "complaint": "bagimli ekiplerden onay beklerken sessiz kalma",
            "theme": "bagimlilik yonetimi",
        },
        {
            "strength": "teknik riskleri erken isaretleme",
            "complaint": "risk etkisini sayisal olarak ifade etmeme",
            "theme": "teknik risk gorunurlugu",
        },
        {
            "strength": "kullanici senaryosu dusunme",
            "complaint": "happy path disi akislarin gec test edilmesi",
            "theme": "kullanici senaryolari",
        },
        {
            "strength": "refactor firsatlarini yakalama",
            "complaint": "refactor kapsam sinirini net cizememe",
            "theme": "refactor kapsami",
        },
        {
            "strength": "release notu hazirlama",
            "complaint": "release etkisini paydaslara gec duyurma",
            "theme": "release iletisimi",
        },
        {
            "strength": "analitik event takibi",
            "complaint": "olcumleme eventlerini sonradan ekleme",
            "theme": "urun analitigi",
        },
        {
            "strength": "tasarim geri bildirimini hizli uygulama",
            "complaint": "tasarim kararlarini kod yorumunda gec aciklama",
            "theme": "tasarim geri bildirimi",
        },
        {
            "strength": "test verisi hazirlama",
            "complaint": "mock veri varyasyonlarini sinirli tutma",
            "theme": "test verisi cesitliligi",
        },
        {
            "strength": "design token tutarliligi",
            "complaint": "renk ve spacing tokenlarini gec standardize etme",
            "theme": "design token yonetimi",
        },
        {
            "strength": "kullanim hatalarini hizli yakalama",
            "complaint": "empty state senaryolarini gec ele alma",
            "theme": "empty state deneyimi",
        },
        {
            "strength": "tablo filtre deneyimini iyilestirme",
            "complaint": "filtre kombinasyonlarini eksik test etme",
            "theme": "liste filtreleme deneyimi",
        },
    ]
    sales_focuses = [
        {
            "strength": "musteri itirazini sakin yonetme",
            "complaint": "itiraz nedenini CRM'e gec isleme",
            "theme": "itiraz yonetimi",
        },
        {
            "strength": "firsat takibini disiplinli surdurme",
            "complaint": "firsat asamasini gec guncelleme",
            "theme": "firsat asamasi takibi",
        },
        {
            "strength": "bolge icgoruslerini paylasma",
            "complaint": "bolge riskini yonetime gec eskale etme",
            "theme": "bolge risk gorunurlugu",
        },
        {
            "strength": "musteri memnuniyeti sinyalini okuma",
            "complaint": "sikayet kok nedenini gec yazma",
            "theme": "musteri memnuniyeti analizi",
        },
        {
            "strength": "teklif sonrasi takip disiplini",
            "complaint": "teklif sonrasi aksiyonu gec kapatma",
            "theme": "teklif takip ritmi",
        },
    ]
    focuses = sales_focuses if dept_key == "sales" else software_focuses
    if dept_key == "software" and "frontend" in normalize_text(employee.team):
        frontend_focus_by_id = {
            399: 0,
            402: 1,
            404: 2,
            407: 3,
            410: 4,
            416: 5,
            418: 6,
            420: 7,
            422: 9,
        }
        if employee.id in frontend_focus_by_id:
            return focuses[frontend_focus_by_id[employee.id]]
    return focuses[((employee.id * 11) + (employee.id // 7)) % len(focuses)]


def build_response_text(plan: FeedbackPlan, dept_key: str) -> str:
    receiver_name = employee_label(plan.receiver)
    sender_name = employee_label(plan.sender)
    context = context_for(dept_key, plan.receiver.team, plan.topic)
    week_label = plan.feedback_date.strftime("%Y-%m-%d")
    personal = personal_patterns(plan.receiver, dept_key)
    strength = personal["strengths"][(plan.sequence + plan.feedback_date.isocalendar().week) % len(personal["strengths"])]
    complaint = personal["complaints"][(plan.sequence + plan.feedback_date.month) % len(personal["complaints"])]
    personal_theme = personal["themes"][(plan.sequence + plan.feedback_date.day) % len(personal["themes"])]
    focus = individual_focus(plan.receiver, dept_key)

    positive_clauses = [
        "somut orneklerle ilerleme paylasmasi ekipte guven olusturdu",
        "destek istemesi ve aldigi geri bildirimi hizla uygulamasi is birligini guclendirdi",
        "zor bir durumda sakin kalip net aksiyon listesi cikarmasi olumlu fark yaratti",
        "ekip arkadaslarina bilgi aktarimi yapmasi ortak tempoyu yukseltti",
    ]
    development_clauses = [
        "ara durum bilgisini daha erken paylasmasi planlama kalitesini artirir",
        "beklentileri netlestirmek icin daha kisa ama sik check-in yapmasi faydali olur",
        "dokumantasyonu ve karar gerekcesini biraz daha gorunur tutmasi gerekiyor",
        "destek ihtiyacini gec soyledigi anlarda diger kisilerin hazirligi zorlasiyor",
    ]
    risk_clauses = [
        "is yuku ve belirsizlik biriktiginde motivasyon dususu belirginlesiyor",
        "blokajlar gec gorunur oldugunda ekip icinde stres ve teslim riski artiyor",
        "ust uste gelen talepler kiside yorulma ve geri cekilme sinyali olusturuyor",
        "net onceliklendirme gelmediginde sahiplenme azalip ayrilma riski yukselebilir",
    ]

    if plan.signal == "risk":
        detail = risk_clauses[(plan.sequence + plan.feedback_date.isocalendar().week) % len(risk_clauses)]
        return (
            f"{week_label} haftasinda {sender_name}, {receiver_name} icin {context} konusunda risk sinyali verdi. "
            f"{detail}. Yonetici tarafinda kapasite konusmasi, oncelik sadeleştirme ve haftalik 1:1 takip onerilir. "
            f"Kisiye ozel tekrar eden konu {complaint}; bireysel odak {focus['complaint']}; is baglami {personal_theme}. "
            "Bu geri bildirim ozellikle motivasyon, psikolojik guven ve ayrilma riski analizinde dikkate alinmalidir."
        )
    if plan.signal == "development":
        detail = development_clauses[(plan.sequence + plan.feedback_date.month) % len(development_clauses)]
        return (
            f"{week_label} haftasinda {sender_name}, {receiver_name} icin {context} alaninda gelisim sinyali paylasti. "
            f"{detail}. Kisi genel olarak katkÄ± veriyor ancak daha gorunur iletisim ve erken destek talebiyle etkisi artar. "
            f"Gelisim notu {complaint} ve {focus['complaint']} etrafinda toplanirken guclu taraf {strength} ve {focus['strength']} olarak gorunuyor. "
            "Bu yorum gelisim, is birligi ve surec disiplini temalarini besler."
        )
    if plan.signal == "strong_positive":
        detail = positive_clauses[(plan.sequence + plan.feedback_date.day) % len(positive_clauses)]
        return (
            f"{week_label} haftasinda {sender_name}, {receiver_name} icin {context} tarafinda cok guclu sinyal verdi. "
            f"{detail}. Bu davranis ekip icinde rol model etkisi yaratti ve psikolojik guveni artirdi. "
            f"Kisiye ozel guclu alan {strength}; bireysel guc {focus['strength']}; one cikan tema {personal_theme}. "
            "Mevcut performans yuksek; mentorluk veya daha kritik sorumlulukla gelisimi desteklenebilir."
        )

    detail = positive_clauses[(plan.sequence + plan.feedback_date.month + plan.feedback_date.day) % len(positive_clauses)]
    return (
        f"{week_label} haftasinda {sender_name}, {receiver_name} icin {context} konusunda dengeli ve olumlu geri bildirim verdi. "
        f"{detail}. Kucuk iyilestirme alani olarak periyodik durum guncellemesi ve beklenti netlestirme one cikiyor. "
        f"Guclu alan {strength}; bireysel guc {focus['strength']}; ikincil takip konusu {complaint} ve {focus['complaint']}. "
        "Genel sinyal motivasyon ve ekip uyumu acisindan pozitif."
    )


def build_week_dates(weeks: int) -> list[datetime]:
    today = datetime.now(timezone.utc).date()
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day_of_month = next_month - timedelta(days=next_month.day)
    anchor_monday = last_day_of_month - timedelta(days=last_day_of_month.weekday())
    if anchor_monday + timedelta(days=2) > last_day_of_month:
        anchor_monday -= timedelta(weeks=1)
    first_monday = anchor_monday - timedelta(weeks=weeks - 1)
    return [
        datetime.combine(first_monday + timedelta(weeks=index, days=2), datetime.min.time(), tzinfo=timezone.utc)
        for index in range(weeks)
    ]


def build_plans_for_department(
    employees: list[Employee],
    *,
    dept_key: str,
    weeks: int,
    feedbacks_per_week: int,
) -> list[FeedbackPlan]:
    by_team: dict[str, list[Employee]] = {}
    for employee in employees:
        by_team.setdefault(employee.team or "Genel", []).append(employee)

    managers = [employee for employee in employees if is_manager(employee, dept_key)]
    non_managers = [employee for employee in employees if not is_manager(employee, dept_key)]
    all_dates = build_week_dates(weeks)
    plans: list[FeedbackPlan] = []

    for week_index, feedback_date in enumerate(all_dates):
        topics = topics_for_week(week_index)
        for employee_index, receiver in enumerate(employees):
            same_team_sender = pick_sender(by_team.get(receiver.team or "Genel", []), receiver, employee_index + week_index + 1)
            cross_team_sender = pick_sender(
                [employee for employee in non_managers if employee.team != receiver.team],
                receiver,
                employee_index + week_index + 3,
            )
            manager_sender = pick_sender(managers, receiver, employee_index + week_index) if not is_manager(receiver, dept_key) else None
            upward_sender = pick_sender(non_managers, receiver, employee_index + week_index + 5) if is_manager(receiver, dept_key) else None

            senders = [same_team_sender, cross_team_sender, manager_sender or upward_sender]
            unique_senders: list[Employee] = []
            for sender in senders:
                if sender and sender.id != receiver.id and sender.id not in {item.id for item in unique_senders}:
                    unique_senders.append(sender)

            for sequence, sender in enumerate(unique_senders[:feedbacks_per_week]):
                topic = topics[sequence % len(topics)]
                plans.append(
                    FeedbackPlan(
                        sender=sender,
                        receiver=receiver,
                        direction=direction_for(sender, receiver, dept_key),
                        signal=signal_for(receiver, week_index, sequence, dept_key),
                        topic=topic,
                        feedback_date=feedback_date + timedelta(hours=9 + sequence * 2),
                        sequence=sequence,
                    )
                )
    return plans


def enrich_analysis_payload(payload: dict, plan: FeedbackPlan, dept_key: str) -> dict:
    topic_labels = {
        "delivery": "Teslim ve planlama",
        "quality": "Kalite ve teknik disiplin" if dept_key == "software" else "Surec ve CRM disiplini",
        "collaboration": "Ekip ici iletisim",
        "leadership": "Yonetsel destek",
        "growth": "Gelisim ve mentorluk",
        "risk": "Is yuku ve risk sinyali",
    }
    signal_label = {
        "risk": "risk sinyali",
        "development": "gelisim alani",
        "positive": "pozitif sinyal",
        "strong_positive": "guclu pozitif sinyal",
    }[plan.signal]
    trend_bucket = plan.receiver.id % 5
    week_index = max(0, min(3, FeedbackService.get_week_of_month(plan.feedback_date.date()) - 1))
    signal_adjustment = {
        "risk": -0.25,
        "development": 0.0,
        "positive": 0.15,
        "strong_positive": 0.3,
    }[plan.signal]

    if trend_bucket == 0:
        motivation = 2.7 + week_index * 0.38 + signal_adjustment
        sentiment = 0.38 + week_index * 0.09 + signal_adjustment * 0.06
        flight_score = 7 - week_index
    elif trend_bucket == 1:
        motivation = 4.2 - week_index * 0.36 + signal_adjustment
        sentiment = 0.72 - week_index * 0.09 + signal_adjustment * 0.05
        flight_score = 3 + week_index
    elif trend_bucket == 2:
        motivation = 3.25 + signal_adjustment * 0.35
        sentiment = 0.55 + signal_adjustment * 0.05
        flight_score = 5
    elif trend_bucket == 3:
        motivation = 3.8 + week_index * 0.18 + signal_adjustment
        sentiment = 0.62 + week_index * 0.05 + signal_adjustment * 0.05
        flight_score = 4
    else:
        motivation = 3.7 - week_index * 0.2 + signal_adjustment
        sentiment = 0.64 - week_index * 0.05 + signal_adjustment * 0.05
        flight_score = 4 + min(2, week_index)

    motivation = round(max(1.0, min(5.0, motivation)), 2)
    sentiment = round(max(0.05, min(0.95, sentiment)), 2)
    flight_score = int(max(1, min(10, flight_score + (1 if plan.signal == "risk" else -1 if plan.signal == "strong_positive" else 0))))
    risk_level = "high" if flight_score >= 7 else "medium" if flight_score >= 5 else "low"

    complaint_map = {
        "delivery": ["blokajlarin gec paylasilmasi", "teslim planinda belirsizlik"],
        "quality": ["kalite kontrol ihtiyaci", "dokumantasyon eksigi"],
        "collaboration": ["ekip ici iletisim kopuklugu", "destek talebinin gecikmesi"],
        "leadership": ["mentorluk ihtiyaci", "beklenti netligi eksigi"],
        "growth": ["gelisim plani ihtiyaci", "ogrenme hedefi belirsizligi"],
        "risk": ["is yuku baskisi", "motivasyon dususu"],
    }
    praise_map = {
        "delivery": ["sorumluluk alma", "teslim takibi"],
        "quality": ["kod kalitesi" if dept_key == "software" else "CRM disiplini", "detaylara dikkat"],
        "collaboration": ["is birligi", "psikolojik guven"],
        "leadership": ["liderlik destegi", "net yonlendirme"],
        "growth": ["gelisime aciklik", "mentorluk katkisi"],
        "risk": ["dayaniklilik", "erken uyari farkindaligi"],
    }
    personal = personal_patterns(plan.receiver, dept_key)
    focus = individual_focus(plan.receiver, dept_key)
    personal_complaints = personal["complaints"]
    personal_strengths = personal["strengths"]
    personal_themes = personal["themes"]

    theme = topic_labels[plan.topic]
    payload["theme_labels"] = list(dict.fromkeys([focus["theme"], personal_themes[0], theme] + personal_themes[1:] + list(payload.get("theme_labels") or [])))[:8]
    payload["entity_mentions"] = list(
        dict.fromkeys([focus["theme"], focus["complaint"], focus["strength"]] + personal_themes + [plan.topic, plan.receiver.team or "Genel", plan.receiver.position or "Rol"] + list(payload.get("entity_mentions") or []))
    )[:10]
    payload["sentiment_score"] = sentiment
    payload["sentiment_label"] = "positive" if sentiment >= 0.62 else "negative" if sentiment <= 0.42 else "neutral"
    payload["motivation_score"] = motivation
    payload["flight_risk_score"] = flight_score
    payload["flight_risk"] = risk_level
    payload["burnout_risk"] = risk_level if plan.signal == "risk" else payload.get("burnout_risk", "low")
    payload["psychological_safety_score"] = round(max(1.0, min(5.0, motivation - 0.1 + (0.2 if plan.topic == "collaboration" else 0))), 2)
    payload["collaboration_score"] = round(max(1.0, min(5.0, motivation + (0.25 if plan.topic == "collaboration" else 0.05))), 2)
    payload["growth_signal_score"] = round(max(1.0, min(5.0, motivation + (0.25 if plan.topic == "growth" else 0))), 2)
    base_complaints = complaint_map[plan.topic] if plan.signal in {"risk", "development"} else complaint_map[plan.topic][:1]
    base_praises = praise_map[plan.topic] if plan.signal in {"positive", "strong_positive"} else praise_map[plan.topic][:1]
    payload["complaint_topics"] = list(dict.fromkeys([focus["complaint"]] + personal_complaints + base_complaints))[:5]
    payload["praise_topics"] = list(dict.fromkeys([focus["strength"]] + personal_strengths + base_praises))[:5]
    payload["key_strengths"] = list(dict.fromkeys([focus["strength"]] + personal_strengths + list(payload.get("key_strengths") or [])))[:5]
    payload["flight_risk_reasons"] = list(dict.fromkeys([focus["complaint"]] + personal_complaints + base_complaints))[:5] if flight_score >= 5 else [focus["complaint"]]
    payload["support_needs"] = list(dict.fromkeys([focus["complaint"]] + personal_complaints[:2] + base_complaints[:1])) if plan.signal in {"risk", "development"} else payload.get("support_needs", [])
    payload["manager_summary"] = (
        f"{employee_label(plan.receiver)} icin {plan.feedback_date.strftime('%B %Y')} haftasinda "
        f"{theme.lower()} alaninda {signal_label} olustu."
    )
    payload["synthetic"] = True
    payload["synthetic_source"] = MODEL_NAME
    payload["synthetic_signal"] = plan.signal
    payload["synthetic_topic"] = plan.topic
    payload["demo_note"] = "Demo 360 feedback history seed verisi; gercek calisan yorumu degildir."
    return payload


def seed_department_history(
    db: Session,
    *,
    department: Department,
    weeks: int,
    feedbacks_per_week: int,
    dry_run: bool,
) -> dict[str, int]:
    dept_key = department_key(department)
    employees = get_department_employees(db, department.id)
    plans = build_plans_for_department(
        employees,
        dept_key=dept_key,
        weeks=weeks,
        feedbacks_per_week=feedbacks_per_week,
    )
    if dry_run:
        return {"employees": len(employees), "planned": len(plans), "created": 0}

    questions: dict[tuple[int, FeedbackDirection, str], FeedbackQuestion] = {}
    created = 0
    profile_periods: set[tuple[int, int, int, int]] = set()
    badge_periods: set[tuple[int, int, int]] = set()

    for plan in plans:
        week_number = FeedbackService.get_week_of_month(plan.feedback_date.date())
        key = (week_number, plan.direction, plan.topic)
        if key not in questions:
            questions[key] = ensure_question(
                db,
                department_id=department.id,
                dept_key=dept_key,
                week_number=week_number,
                direction=plan.direction,
                topic=plan.topic,
            )

        question = questions[key]
        scores = scores_for_signal(plan.signal, plan.topic)
        response_text = build_response_text(plan, dept_key)
        row = FeedbackResponse(
            sender_id=plan.sender.id,
            receiver_id=plan.receiver.id,
            question_id=question.id,
            response_text=response_text,
            score_communication=scores[0],
            score_teamwork=scores[1],
            score_leadership=scores[2],
            score_technical=scores[3],
            period_week=week_number,
            period_month=plan.feedback_date.month,
            period_year=plan.feedback_date.year,
            nlp_analysis=None,
            created_at=plan.feedback_date,
            updated_at=plan.feedback_date,
        )
        db.add(row)
        db.flush()

        analysis_payload = AIService._fallback_weekly_analysis(
            dept_name=department.name,
            question_text=question.question_text,
            response_text=response_text,
            score_communication=float(scores[0]),
            score_teamwork=float(scores[1]),
            score_leadership=float(scores[2]),
            score_technical=float(scores[3]),
        )
        analysis_payload = enrich_analysis_payload(analysis_payload, plan, dept_key)

        analysis = NLPService.save_weekly_analysis(
            db,
            feedback_response=row,
            analysis_payload=analysis_payload,
            analysis_version="synthetic-history-v1",
            model_provider=MODEL_PROVIDER,
            model_name=MODEL_NAME,
        )
        analysis.created_at = plan.feedback_date
        analysis.updated_at = plan.feedback_date

        memory = RAGService.upsert_weekly_feedback_memory(
            db,
            feedback_response=row,
            analysis_payload=analysis_payload,
        )
        memory.created_at = plan.feedback_date
        memory.updated_at = plan.feedback_date

        profile_periods.add((plan.receiver.id, plan.feedback_date.year, plan.feedback_date.month, week_number))
        badge_periods.add((plan.receiver.id, plan.feedback_date.year, plan.feedback_date.month))
        created += 1

    for employee_id, year, month, week in sorted(profile_periods):
        NLPService.rebuild_employee_profile(
            db,
            employee_id=employee_id,
            period_type=NLPPeriodType.weekly,
            period_year=year,
            period_month=month,
            period_week=week,
        )
    for employee_id, year, month in sorted(badge_periods):
        NLPService.refresh_employee_monthly_badges(
            db,
            employee_id=employee_id,
            period_year=year,
            period_month=month,
        )

    db.commit()
    return {"employees": len(employees), "planned": len(plans), "created": created}


def seed_history(
    db: Session,
    *,
    target: str,
    weeks: int,
    feedbacks_per_week: int,
    reset: bool,
    dry_run: bool,
) -> dict[str, int]:
    departments = get_target_departments(db, target)
    deleted = clear_existing_synthetic_rows(db) if reset and not dry_run else 0
    totals = {"departments": len(departments), "employees": 0, "planned": 0, "created": 0, "deleted": deleted}

    for department in departments:
        result = seed_department_history(
            db,
            department=department,
            weeks=weeks,
            feedbacks_per_week=feedbacks_per_week,
            dry_run=dry_run,
        )
        totals["employees"] += result["employees"]
        totals["planned"] += result["planned"]
        totals["created"] += result["created"]

    return totals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Yazilim ve satis icin 3 aylik, calisan basina haftada 3 adet demo 360 NLP history seed eder."
    )
    parser.add_argument("--department", choices=["all", "software", "sales"], default="all")
    parser.add_argument("--weeks", type=int, default=DEFAULT_WEEKS)
    parser.add_argument("--feedbacks-per-week", type=int, choices=[1, 2, 3], default=DEFAULT_FEEDBACKS_PER_WEEK)
    parser.add_argument("--no-reset", action="store_true", help="Onceki synthetic_seed_360_history kayitlarini temizleme.")
    parser.add_argument("--dry-run", action="store_true", help="Kayit yazmadan planlanan sayilari goster.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        result = seed_history(
            db,
            target=args.department,
            weeks=args.weeks,
            feedbacks_per_week=args.feedbacks_per_week,
            reset=not args.no_reset,
            dry_run=args.dry_run,
        )
        print(
            "360 history seed tamamlandi: "
            f"{result['departments']} departman, {result['employees']} calisan, "
            f"{result['created']} yeni feedback/NLP/RAG kaydi, {result['deleted']} eski synthetic kayit temizlendi."
        )
        if args.dry_run:
            print(f"Dry-run planlanan feedback sayisi: {result['planned']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
