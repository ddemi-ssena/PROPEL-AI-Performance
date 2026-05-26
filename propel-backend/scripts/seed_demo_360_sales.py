from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackDirection, FeedbackQuestion, FeedbackResponse
from app.db.models.nlp import FeedbackNLPAnalysis, NLPPeriodType
from app.db.session import SessionLocal
from app.services.ai_service import AIService
from app.services.feedback_service import FeedbackService
from app.services.nlp_service import NLPService


MODEL_PROVIDER = "synthetic_seed_sales"
MODEL_NAME = "demo-360-sales-v1"
DEFAULT_RESPONSES_PER_EMPLOYEE = 3


@dataclass(frozen=True)
class FeedbackPlan:
    sender: Employee
    receiver: Employee
    direction: FeedbackDirection
    signal: str


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    for src, tgt in {"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c", "İ": "i"}.items():
        text = text.replace(src, tgt)
    return text


def get_sales_department(db: Session) -> Department:
    departments = db.query(Department).all()
    for dept in departments:
        normalized = normalize_text(dept.name)
        if "satis" in normalized or "sat" in normalized:
            return dept
    raise RuntimeError("Satis departmani bulunamadi.")


def get_sales_employees(db: Session, department_id: int) -> list[Employee]:
    employees = (
        db.query(Employee)
        .filter(Employee.department_id == department_id)
        .order_by(Employee.team.asc(), Employee.id.asc())
        .all()
    )
    if len(employees) < 4:
        raise RuntimeError("Demo 360 verisi icin yeterli satis calisani yok.")
    return employees


def clear_existing_synthetic_rows(db: Session) -> int:
    analyses = (
        db.query(FeedbackNLPAnalysis)
        .filter(FeedbackNLPAnalysis.model_provider == MODEL_PROVIDER)
        .all()
    )
    response_ids = [a.weekly_feedback_id for a in analyses if a.weekly_feedback_id]
    deleted = len(response_ids)
    for a in analyses:
        db.delete(a)
    db.flush()
    if response_ids:
        db.query(FeedbackResponse).filter(FeedbackResponse.id.in_(response_ids)).delete(synchronize_session=False)
    db.commit()
    return deleted


def question_text(direction: FeedbackDirection) -> str:
    if direction == FeedbackDirection.manager_to_employee:
        return (
            "Son hafta bu satis temsilcisinin musterilerle iliskileri, quota performansi ve takim icindeki "
            "is birligi davranislarini somut bir ornekle degerlendirir misiniz?"
        )
    if direction == FeedbackDirection.employee_to_manager:
        return (
            "Son hafta yoneticinizin satis hedef yonetimi, baskiyi dengeleme ve ekip motivasyonuna katkisi "
            "acisindan somut bir durumu nasil degerlendiriyorsunuz?"
        )
    return (
        "Son hafta birlikte calisirken bu kisinin musteri iletisimi, is birligi ve satis surec disiplini "
        "acisindan somut bir ornekle ne gozlemlediniz?"
    )


def ensure_question(db: Session, department_id: int, week_number: int, direction: FeedbackDirection) -> FeedbackQuestion:
    question = (
        db.query(FeedbackQuestion)
        .filter(
            FeedbackQuestion.department_id == department_id,
            FeedbackQuestion.week_number == week_number,
            FeedbackQuestion.direction == direction,
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
        question_text=question_text(direction),
        category="Demo 360 Satis NLP sinyali",
        is_ai_generated=False,
    )
    db.add(question)
    db.flush()
    return question


def employee_label(employee: Employee) -> str:
    if employee.user:
        full_name = str(getattr(employee.user, "full_name", "") or "").strip()
        if full_name:
            return full_name
    return employee.external_employee_code or f"Calisan #{employee.id}"


def choose_signal(receiver: Employee, index: int) -> str:
    team = normalize_text(receiver.team)
    # Manager/Genel bolgesi
    if "genel" in team:
        return ["development", "positive", "development", "positive"][index % 4]
    # Riskli bolgeler (Dogu Anadolu, Guneydogu genelde riskli profiller)
    if "dogu" in team or "guneydogu" in team:
        return ["risk", "development", "risk", "development"][index % 4]
    if "karadeniz" in team:
        return ["development", "risk", "development", "positive"][index % 4]
    if "marmara" in team or "ege" in team:
        return ["positive", "development", "positive", "development"][index % 4]
    if "akdeniz" in team:
        return ["development", "positive", "risk", "development"][index % 4]
    if "ic anadolu" in team or "ic" in team:
        return ["development", "positive", "development", "risk"][index % 4]
    return ["positive", "development", "positive", "risk"][index % 4]


def scores_for_signal(signal: str, receiver: Employee) -> tuple[int, int, int, int]:
    team = normalize_text(receiver.team)
    if signal == "risk":
        if "dogu" in team or "guneydogu" in team:
            return 2, 2, 2, 3
        return 3, 2, 2, 3
    if signal == "development":
        if "marmara" in team or "ege" in team:
            return 4, 3, 3, 4
        return 3, 3, 3, 4
    if signal == "strong_positive":
        return 5, 5, 4, 5
    return 4, 4, 4, 4


def context_for_team(team: str | None) -> str:
    normalized = normalize_text(team)
    if "marmara" in normalized:
        return "buyuk hesap yonetimi, kurumsal musteri ziyaretleri ve tekliften kazanima geciste"
    if "ege" in normalized:
        return "bolge musteri portfoyu, yeni musteri edinimi ve CRM takibinde"
    if "karadeniz" in normalized:
        return "pipeline yonetimi, satis dongusu suresi ve bolge kapanislarinda"
    if "akdeniz" in normalized:
        return "musteri memnuniyeti takibi, sikayet yonetimi ve tekrarlayan satis surecinde"
    if "dogu" in normalized:
        return "yuksek is yuku altinda quota basinci, sahada musteri toplantilari ve destek gereksinimi konularinda"
    if "guneydogu" in normalized:
        return "zorlu bolge kosullarinda musteri iliskisi, satis aktivite yogunlugu ve ekip desteginde"
    if "ic anadolu" in normalized or "ic" in normalized:
        return "orta bant hesap yonetimi, bolge stratejisi ve takim koordinasyonunda"
    if "genel" in normalized:
        return "ekip yonetimi, hedef belirleme, satis strateji koordinasyonu ve departman birlesik performansinda"
    return "haftalik satis akisi ve musteri iliskisi surecinde"


def build_response_text(plan: FeedbackPlan, question: FeedbackQuestion) -> str:
    receiver_name = employee_label(plan.receiver)
    context = context_for_team(plan.receiver.team)
    hint = "Sorunun odagina uygun olarak"

    if plan.signal == "risk":
        return (
            f"{hint}, son hafta {receiver_name} icin {context} belirgin baski ve blokaj olustu. "
            "Quota basinci, musteri toplamlarinin gecikmesi ve bolgede artan is yuku motivasyon dususune neden olabiliyor. "
            "Kisi satis aktivitelerini surduruyor ancak destek istemekte gecikiyor; "
            "bu durum hata oranini ve sikayet riskini artirabilir. "
            "Daha erken yonetici check-in ve net onceliklendirme yardimci olacaktir."
        )
    if plan.signal == "development":
        return (
            f"{hint}, {receiver_name} son haftada {context} teknik ve surec acisindan guvenilir katkı verdi. "
            "Bununla birlikte bazi musteri durum guncellemelerini gec paylasmasi CRM kaytlarini aksatiyordu. "
            "Pipeline disiplinini ve sikayet dokumantasyonunu kuvvetlendirirse hem kalite hem is birligi iyilesecek. "
            "Genel sinyaller gelisim yonunde; kucuk adimlarla ilerleme hizi artabilir."
        )
    if plan.signal == "strong_positive":
        return (
            f"{hint}, {receiver_name} {context} cok guvenilir ve destekleyici bir performans sergiledi. "
            "Musteri sorunlarini sahiplenip hizli kapamasi, quota atainment'ini ust bantlarda tutmasi "
            "ve ekip arkdaslarina yonlendirme yaparak destek vermesi dikkat cekiciydi. "
            "Bu davranis diger bolge temsilcileri icin pozitif bir referans noktasi olusturuyor."
        )
    return (
        f"{hint}, {receiver_name} son hafta {context} dengeli ve sistematik bir katkı verdi. "
        "Musteri takiplerini zamaninda tamamladi, pipeline'ini guncelledi ve bolge kapanisi icin plan yapti. "
        "Yogun haftalarda ara guncellemelerini artirirsa satin alma surecindeki belirsizlikler azalacak; "
        "genel sinyal uretkenlik ve ekip uyumu acisindan pozitif."
    )


def direction_for(sender: Employee, receiver: Employee) -> FeedbackDirection:
    sender_team = normalize_text(sender.team)
    receiver_team = normalize_text(receiver.team)
    if "genel" in sender_team and "genel" not in receiver_team:
        return FeedbackDirection.manager_to_employee
    if "genel" not in sender_team and "genel" in receiver_team:
        return FeedbackDirection.employee_to_manager
    return FeedbackDirection.peer_to_peer


def pick_sender(candidates: Iterable[Employee], receiver: Employee, offset: int) -> Employee | None:
    ordered = [e for e in candidates if e.id != receiver.id]
    if not ordered:
        return None
    ordered = sorted(ordered, key=lambda e: (e.external_employee_code or "", e.id))
    return ordered[offset % len(ordered)]


def build_plans(employees: list[Employee], responses_per_employee: int) -> list[FeedbackPlan]:
    by_team: dict[str, list[Employee]] = {}
    for emp in employees:
        by_team.setdefault(emp.team or "Genel", []).append(emp)

    managers = [e for e in employees if normalize_text(e.team) == "genel"]
    non_managers = [e for e in employees if normalize_text(e.team) != "genel"]
    plans: list[FeedbackPlan] = []

    for index, receiver in enumerate(employees):
        same_team_sender = pick_sender(by_team.get(receiver.team or "Genel", []), receiver, index + 1)
        cross_team_sender = pick_sender(
            [e for e in non_managers if e.team != receiver.team],
            receiver,
            index + 2,
        )
        manager_sender = pick_sender(managers, receiver, index) if normalize_text(receiver.team) != "genel" else None
        upward_sender = pick_sender(non_managers, receiver, index + 3) if normalize_text(receiver.team) == "genel" else None

        senders = [same_team_sender, cross_team_sender, manager_sender or upward_sender]
        unique_senders: list[Employee] = []
        for sender in senders:
            if sender and sender.id != receiver.id and sender.id not in {s.id for s in unique_senders}:
                unique_senders.append(sender)

        for sig_index, sender in enumerate(unique_senders[:responses_per_employee]):
            plans.append(
                FeedbackPlan(
                    sender=sender,
                    receiver=receiver,
                    direction=direction_for(sender, receiver),
                    signal=choose_signal(receiver, sig_index + index),
                )
            )
    return plans


def seed_demo_360_sales(db: Session, *, reset: bool, responses_per_employee: int, dry_run: bool) -> dict[str, int]:
    department = get_sales_department(db)
    employees = get_sales_employees(db, department.id)
    week_number = FeedbackService.get_week_of_month()
    now = datetime.now(timezone.utc)

    deleted = clear_existing_synthetic_rows(db) if reset and not dry_run else 0
    plans = build_plans(employees, responses_per_employee)
    if dry_run:
        return {"employees": len(employees), "planned_responses": len(plans), "deleted": deleted, "created": 0}

    questions = {
        direction: ensure_question(db, department.id, week_number, direction)
        for direction in {
            FeedbackDirection.peer_to_peer,
            FeedbackDirection.manager_to_employee,
            FeedbackDirection.employee_to_manager,
        }
    }

    created = 0
    profile_employee_ids: set[int] = set()
    for plan in plans:
        question = questions[plan.direction]
        scores = scores_for_signal(plan.signal, plan.receiver)
        response_text = build_response_text(plan, question)
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
            period_month=now.month,
            period_year=now.year,
            nlp_analysis=None,
            created_at=now,
            updated_at=now,
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
        analysis_payload["synthetic"] = True
        analysis_payload["synthetic_source"] = MODEL_NAME
        analysis_payload["demo_note"] = "Demo 360 satis feedback seed verisi; gercek calisan yorumu degildir."

        analysis = NLPService.save_weekly_analysis(
            db,
            feedback_response=row,
            analysis_payload=analysis_payload,
            analysis_version="synthetic-demo-v1",
            model_provider=MODEL_PROVIDER,
            model_name=MODEL_NAME,
        )
        analysis.created_at = now
        analysis.updated_at = now
        profile_employee_ids.add(plan.receiver.id)
        created += 1

    for employee_id in profile_employee_ids:
        NLPService.rebuild_employee_profile(
            db,
            employee_id=employee_id,
            period_type=NLPPeriodType.weekly,
            period_year=now.year,
            period_month=now.month,
            period_week=week_number,
        )
        NLPService.refresh_employee_monthly_badges(
            db,
            employee_id=employee_id,
            period_year=now.year,
            period_month=now.month,
        )

    db.commit()
    return {"employees": len(employees), "planned_responses": len(plans), "deleted": deleted, "created": created}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Satis departmani icin demo 360 feedback ve NLP analizi seed eder.")
    parser.add_argument("--no-reset", action="store_true", help="Onceki synthetic_seed_sales kayitlarini temizleme.")
    parser.add_argument(
        "--responses-per-employee",
        type=int,
        default=DEFAULT_RESPONSES_PER_EMPLOYEE,
        choices=[1, 2, 3],
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        result = seed_demo_360_sales(
            db,
            reset=not args.no_reset,
            responses_per_employee=args.responses_per_employee,
            dry_run=args.dry_run,
        )
        print(
            "Satis 360 seed tamamlandi: "
            f"{result['employees']} calisan, {result['created']} yeni feedback/NLP kaydi, "
            f"{result['deleted']} eski synthetic kayit temizlendi."
        )
        if args.dry_run:
            print(f"Dry-run planlanan feedback sayisi: {result['planned_responses']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
