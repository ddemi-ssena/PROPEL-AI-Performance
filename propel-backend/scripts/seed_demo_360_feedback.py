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


MODEL_PROVIDER = "synthetic_seed"
MODEL_NAME = "demo-360-software-v1"
DEFAULT_RESPONSES_PER_EMPLOYEE = 3


@dataclass(frozen=True)
class FeedbackPlan:
    sender: Employee
    receiver: Employee
    direction: FeedbackDirection
    signal: str


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    replacements = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
        "İ": "i",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def get_software_department(db: Session) -> Department:
    departments = db.query(Department).all()
    for department in departments:
        normalized = normalize_text(department.name)
        if "yazilim" in normalized or "software" in normalized:
            return department
    raise RuntimeError("Yazilim departmani bulunamadi.")


def get_software_employees(db: Session, department_id: int) -> list[Employee]:
    employees = (
        db.query(Employee)
        .filter(Employee.department_id == department_id)
        .order_by(Employee.team.asc(), Employee.id.asc())
        .all()
    )
    if len(employees) < 4:
        raise RuntimeError("Demo 360 verisi icin yeterli yazilim calisani yok.")
    return employees


def clear_existing_synthetic_rows(db: Session) -> int:
    analyses = (
        db.query(FeedbackNLPAnalysis)
        .filter(FeedbackNLPAnalysis.model_provider == MODEL_PROVIDER)
        .all()
    )
    response_ids = [analysis.weekly_feedback_id for analysis in analyses if analysis.weekly_feedback_id]
    deleted = len(response_ids)
    for analysis in analyses:
        db.delete(analysis)
    db.flush()
    if response_ids:
        (
            db.query(FeedbackResponse)
            .filter(FeedbackResponse.id.in_(response_ids))
            .delete(synchronize_session=False)
        )
    db.commit()
    return deleted


def question_text(direction: FeedbackDirection) -> str:
    if direction == FeedbackDirection.manager_to_employee:
        return (
            "Son hafta bu calisanin ekip icindeki is birligi, destek alma/verme ve motivasyon sinyallerini "
            "somut bir ornekle anlatir misiniz?"
        )
    if direction == FeedbackDirection.employee_to_manager:
        return (
            "Son hafta yoneticinizin netlik, destek, psikolojik guven ve is yukunu dengeleme davranislarini "
            "somut bir durum uzerinden nasil deneyimlediniz?"
        )
    return (
        "Son hafta birlikte calisirken bu kisinin iletisim, is birligi, guven ve destek davranislarini "
        "somut bir ornekle nasil gozlemlediniz?"
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
        category="Demo 360 NLP sinyali",
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
    if "qa" in team:
        return ["risk", "development", "development", "positive"][index % 4]
    if "backend" in team:
        return ["development", "risk", "positive", "development"][index % 4]
    if "frontend" in team:
        return ["positive", "development", "positive", "risk"][index % 4]
    if "devops" in team:
        return ["positive", "development", "positive", "development"][index % 4]
    if "yonetim" in team or "management" in team:
        return ["development", "positive", "development", "risk"][index % 4]
    return ["positive", "development", "positive", "risk"][index % 4]


def scores_for_signal(signal: str, receiver: Employee) -> tuple[int, int, int, int]:
    team = normalize_text(receiver.team)
    if signal == "risk":
        if "qa" in team:
            return 2, 3, 2, 3
        if "backend" in team:
            return 3, 2, 2, 3
        return 3, 3, 2, 3
    if signal == "development":
        if "backend" in team or "qa" in team:
            return 3, 3, 3, 4
        return 4, 3, 3, 4
    if signal == "strong_positive":
        return 5, 5, 4, 5
    return 4, 4, 4, 4


def context_for_team(team: str | None) -> str:
    normalized = normalize_text(team)
    if "backend" in normalized:
        return "API entegrasyonu, code review ve sprint teslim planinda"
    if "frontend" in normalized:
        return "arayuz teslimi, tasarim uyumu ve backend bagimliliklarinda"
    if "qa" in normalized:
        return "test senaryolari, regresyon takibi ve hata geri donuslerinde"
    if "devops" in normalized:
        return "deploy, ortam stabilitesi ve operasyonel destek akisi icinde"
    if "yonetim" in normalized:
        return "onceliklendirme, ekipler arasi koordinasyon ve karar netliginde"
    return "haftalik sprint akisi ve ekip koordinasyonunda"


def build_response_text(plan: FeedbackPlan, question: FeedbackQuestion) -> str:
    receiver_name = employee_label(plan.receiver)
    sender_team = plan.sender.team or "ekip"
    context = context_for_team(plan.receiver.team)
    question_hint = "Sorunun odagina uygun olarak"

    if plan.signal == "risk":
        return (
            f"{question_hint}, son hafta {receiver_name} icin {context} belirgin bir baski olusturdu. "
            "Kisi teknik olarak katkı vermeye calisiyor ancak deadline baskisi, blokaj ve toplantı yogunlugu nedeniyle "
            "destek istemekte gecikebiliyor. Bu durum ekipte iletisim yavaslamasi ve motivasyon dususu yaratabilir. "
            f"{sender_team} tarafindan daha erken kapasite konusmasi ve net onceliklendirme yapilmasi iyi olur."
        )
    if plan.signal == "development":
        return (
            f"{question_hint}, {receiver_name} son sprintte {context} teknik olarak guvenilir katkı verdi. "
            "Bununla birlikte bazi durumlarda ilerleme bilgisini gec paylasmasi diger ekiplerin planlama yapmasini zorlastirdi. "
            "Daha seffaf ara bilgilendirme, code review beklentilerinin netlesmesi ve destek ihtiyacinin erken soylenmesi "
            "hem is birligini hem psikolojik guveni guclendirir."
        )
    if plan.signal == "strong_positive":
        return (
            f"{question_hint}, {receiver_name} {context} guven veren ve destekleyici bir rol ustlendi. "
            "Sorunlari sahiplenmesi, hizli donus yapmasi ve yapici geri bildirim vermesi ekip uyumunu guclendirdi. "
            "Bu davranis motivasyonu artiriyor ve diger kisilerin de acik sekilde destek istemesini kolaylastiriyor."
        )
    return (
        f"{question_hint}, {receiver_name} son hafta {context} olumlu ve dengeli bir katkı verdi. "
        "Iletisimi genel olarak acikti, ekip arkadaslarina destek oldu ve teknik konularda cozum odakli davrandi. "
        "Yogun zamanlarda daha erken durum guncellemesi yaparsa is birligi daha da rahatlar; genel sinyal guven ve uyum acisindan pozitif."
    )


def direction_for(sender: Employee, receiver: Employee) -> FeedbackDirection:
    sender_team = normalize_text(sender.team)
    receiver_team = normalize_text(receiver.team)
    if "yonetim" in sender_team and "yonetim" not in receiver_team:
        return FeedbackDirection.manager_to_employee
    if "yonetim" not in sender_team and "yonetim" in receiver_team:
        return FeedbackDirection.employee_to_manager
    return FeedbackDirection.peer_to_peer


def pick_sender(candidates: Iterable[Employee], receiver: Employee, offset: int) -> Employee | None:
    ordered = [employee for employee in candidates if employee.id != receiver.id]
    if not ordered:
        return None
    ordered = sorted(ordered, key=lambda item: (item.external_employee_code or "", item.id))
    return ordered[offset % len(ordered)]


def build_plans(employees: list[Employee], responses_per_employee: int) -> list[FeedbackPlan]:
    by_team: dict[str, list[Employee]] = {}
    for employee in employees:
        by_team.setdefault(employee.team or "Genel", []).append(employee)

    managers = [employee for employee in employees if normalize_text(employee.team) == "yonetim"]
    non_managers = [employee for employee in employees if normalize_text(employee.team) != "yonetim"]
    plans: list[FeedbackPlan] = []

    for index, receiver in enumerate(employees):
        same_team_sender = pick_sender(by_team.get(receiver.team or "Genel", []), receiver, index + 1)
        cross_team_sender = pick_sender(
            [employee for employee in non_managers if employee.team != receiver.team],
            receiver,
            index + 2,
        )
        manager_sender = pick_sender(managers, receiver, index) if normalize_text(receiver.team) != "yonetim" else None
        upward_sender = pick_sender(non_managers, receiver, index + 3) if normalize_text(receiver.team) == "yonetim" else None

        senders = [same_team_sender, cross_team_sender, manager_sender or upward_sender]
        unique_senders: list[Employee] = []
        for sender in senders:
            if sender and sender.id != receiver.id and sender.id not in {item.id for item in unique_senders}:
                unique_senders.append(sender)

        for signal_index, sender in enumerate(unique_senders[:responses_per_employee]):
            plans.append(
                FeedbackPlan(
                    sender=sender,
                    receiver=receiver,
                    direction=direction_for(sender, receiver),
                    signal=choose_signal(receiver, signal_index + index),
                )
            )
    return plans


def seed_demo_360(db: Session, *, reset: bool, responses_per_employee: int, dry_run: bool) -> dict[str, int]:
    department = get_software_department(db)
    employees = get_software_employees(db, department.id)
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
        analysis_payload["demo_note"] = "Demo 360 feedback seed verisi; gercek calisan yorumu degildir."

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
    parser = argparse.ArgumentParser(description="Yazilim departmani icin demo 360 feedback ve NLP analizi seed eder.")
    parser.add_argument("--no-reset", action="store_true", help="Onceki synthetic_seed kayitlarini temizleme.")
    parser.add_argument(
        "--responses-per-employee",
        type=int,
        default=DEFAULT_RESPONSES_PER_EMPLOYEE,
        choices=[1, 2, 3],
        help="Her calisan icin olusturulacak incoming feedback sayisi.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Kayit yazmadan planlanan sayilari goster.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        result = seed_demo_360(
            db,
            reset=not args.no_reset,
            responses_per_employee=args.responses_per_employee,
            dry_run=args.dry_run,
        )
        print(
            "Demo 360 seed tamamlandi: "
            f"{result['employees']} calisan, {result['created']} yeni feedback/NLP kaydi, "
            f"{result['deleted']} eski synthetic kayit temizlendi."
        )
        if args.dry_run:
            print(f"Dry-run planlanan feedback sayisi: {result['planned_responses']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
