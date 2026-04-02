from __future__ import annotations

from datetime import datetime

from app.db.session import SessionLocal
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackDirection, FeedbackQuestion, FeedbackResponse
from app.db.models.nlp import NLPPeriodType
from app.db.models.user import UserRole
from app.services.ai_service import AIService
from app.services.feedback_service import FeedbackService
from app.services.nlp_service import NLPService
from app.services.rag_service import RAGService


SCENARIOS = [
    {
        "employee_id": 79,
        "employee_name": "Canan Dagdelen",
        "direction": "positive_stable",
        "entries": [
            {
                "sender_id": 80,
                "sender_role": UserRole.employee,
                "week_number": 1,
                "category": "Surecler & Blokajlar",
                "question_text": "Bu hafta is akisinda bir blokaj yasadiginda bu kisinin sureci sahiplenme ve cozum uretme davranisini nasil degerlendirirsin?",
                "response_text": "Blokaj yasadiginda sakin kaldi ve cozum bulmak icin hizla harekete gecti. Teknik borc olusturmadan ilerlemeye dikkat etti ve ekibin surece guvenini yuksek tuttu.",
                "scores": (5, 4, 4, 5),
                "created_at": datetime(2026, 3, 3, 10, 15, 0),
            },
            {
                "sender_id": 76,
                "sender_role": UserRole.department_manager,
                "week_number": 2,
                "category": "Motivasyon & Psikolojik Durum",
                "question_text": "Bu hafta yogun sprint temposunda bu kisinin motivasyonu ve sorumluluk alma istegi nasil gorunuyordu?",
                "response_text": "Enerjisi yuksekti ve yeni kutuphaneleri denemeye istekliydi. Ekip hedeflerine inanci guclu ve zorlandigi anlarda bile olumlu tutumunu koruyor.",
                "scores": (4, 5, 4, 5),
                "created_at": datetime(2026, 3, 10, 11, 30, 0),
            },
            {
                "sender_id": 81,
                "sender_role": UserRole.employee,
                "week_number": 3,
                "category": "Is Birligi & Seffaflik",
                "question_text": "Bu hafta ekip ici iletisim ve yardimlasma acisindan bu kisinin davranisi nasildi?",
                "response_text": "Code review yorumlari yapiciydi ve yardim istendiginde hizli donus sagladi. Ekipte guven veren, acik ve destekleyici bir iletisim kurdu.",
                "scores": (5, 5, 4, 4),
                "created_at": datetime(2026, 3, 17, 15, 0, 0),
            },
        ],
    },
    {
        "employee_id": 81,
        "employee_name": "Elif Ozturk",
        "direction": "burnout_flight_risk",
        "entries": [
            {
                "sender_id": 79,
                "sender_role": UserRole.employee,
                "week_number": 1,
                "category": "Surecler & Blokajlar",
                "question_text": "Bu hafta is akisinda bir blokaj yasadiginda bu kisinin sureci sahiplenme ve cozum uretme davranisini nasil degerlendirirsin?",
                "response_text": "Toplanti yogunlugu ve deadline baskisi yuzunden cok yorulmus gorundu. Surecler yavasladiginda cabuk dusuyor ve blokajlari cozmek yerine geri cekiliyor.",
                "scores": (2, 2, 2, 2),
                "created_at": datetime(2026, 3, 4, 9, 45, 0),
            },
            {
                "sender_id": 76,
                "sender_role": UserRole.department_manager,
                "week_number": 2,
                "category": "Motivasyon & Psikolojik Durum",
                "question_text": "Bu hafta yogun sprint temposunda bu kisinin motivasyonu ve sorumluluk alma istegi nasil gorunuyordu?",
                "response_text": "Teknik blokajlar uzun surunce motivasyonu belirgin sekilde dustu. Ekip hedeflerine olan inanci zayifladi ve artik eskisi kadar sahiplenmedigini hissettiriyor.",
                "scores": (2, 2, 2, 2),
                "created_at": datetime(2026, 3, 11, 13, 10, 0),
            },
            {
                "sender_id": 82,
                "sender_role": UserRole.employee,
                "week_number": 3,
                "category": "Is Birligi & Seffaflik",
                "question_text": "Bu hafta ekip ici iletisim ve yardimlasma acisindan bu kisinin davranisi nasildi?",
                "response_text": "Code review toplantilarina isteksiz katiliyor ve yardim istemekten kacinıyor. Son gunlerde isiyle baginin zayifladigi ve surecleri artik cok onemsemedigi izlenimini veriyor.",
                "scores": (2, 1, 2, 2),
                "created_at": datetime(2026, 3, 18, 16, 20, 0),
            },
        ],
    },
    {
        "employee_id": 82,
        "employee_name": "Murat Kaya",
        "direction": "mixed_recovery",
        "entries": [
            {
                "sender_id": 79,
                "sender_role": UserRole.employee,
                "week_number": 1,
                "category": "Surecler & Blokajlar",
                "question_text": "Bu hafta is akisinda bir blokaj yasadiginda bu kisinin sureci sahiplenme ve cozum uretme davranisini nasil degerlendirirsin?",
                "response_text": "Haftanin basinda task takibi ve dokumantasyon tarafinda daginikti. Sureci toparlamakta zorlansa da geri bildirim aldiginda savunmaci olmadi.",
                "scores": (3, 3, 2, 3),
                "created_at": datetime(2026, 3, 5, 10, 5, 0),
            },
            {
                "sender_id": 76,
                "sender_role": UserRole.department_manager,
                "week_number": 2,
                "category": "Motivasyon & Psikolojik Durum",
                "question_text": "Bu hafta yogun sprint temposunda bu kisinin motivasyonu ve sorumluluk alma istegi nasil gorunuyordu?",
                "response_text": "Mentorluk aldiginda toparlanmaya basladi ve yeni kutuphaneleri ogrenmeye daha acik gorundu. Ozguveni dalgalansa da ekibe katkı verme istegi geri donuyor.",
                "scores": (3, 3, 3, 4),
                "created_at": datetime(2026, 3, 12, 14, 10, 0),
            },
            {
                "sender_id": 81,
                "sender_role": UserRole.employee,
                "week_number": 3,
                "category": "Is Birligi & Seffaflik",
                "question_text": "Bu hafta ekip ici iletisim ve yardimlasma acisindan bu kisinin davranisi nasildi?",
                "response_text": "Bu hafta iletisimi daha seffafti ve destek isteme davranisi artti. Stresli anlarda hala kararsizlasiyor ama ekip uyumu gecen haftalara gore daha iyi.",
                "scores": (4, 4, 3, 4),
                "created_at": datetime(2026, 3, 19, 11, 25, 0),
            },
        ],
    },
]


def direction_label(direction: FeedbackDirection) -> str:
    labels = {
        FeedbackDirection.manager_to_employee: "Yoneticiden Calisana",
        FeedbackDirection.employee_to_manager: "Calisandan Yoneticiye",
        FeedbackDirection.peer_to_peer: "Es Degerlendirme",
        FeedbackDirection.manager_to_manager: "Yonetici - Yonetici",
        FeedbackDirection.employee_to_employee: "Calisan - Calisan",
    }
    return labels.get(direction, "Es Degerlendirme")


def upsert_question(db, *, week_number: int, direction: FeedbackDirection, category: str, department_id: int | None, question_text: str) -> FeedbackQuestion:
    question = db.query(FeedbackQuestion).filter(
        FeedbackQuestion.week_number == week_number,
        FeedbackQuestion.direction == direction,
        FeedbackQuestion.category == category,
        FeedbackQuestion.department_id == department_id,
        FeedbackQuestion.question_text == question_text,
    ).first()
    if question:
        return question

    question = FeedbackQuestion(
        week_number=week_number,
        direction=direction,
        category=category,
        department_id=department_id,
        question_text=question_text,
        is_ai_generated=True,
    )
    db.add(question)
    db.flush()
    return question


def upsert_response(db, *, sender_id: int, receiver_id: int, question_id: int, response_text: str, scores: tuple[int, int, int, int], created_at: datetime, week_number: int) -> FeedbackResponse:
    row = db.query(FeedbackResponse).filter(
        FeedbackResponse.sender_id == sender_id,
        FeedbackResponse.receiver_id == receiver_id,
        FeedbackResponse.question_id == question_id,
        FeedbackResponse.period_week == week_number,
        FeedbackResponse.period_month == created_at.month,
        FeedbackResponse.period_year == created_at.year,
    ).first()

    payload = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "question_id": question_id,
        "response_text": response_text,
        "score_communication": scores[0],
        "score_teamwork": scores[1],
        "score_leadership": scores[2],
        "score_technical": scores[3],
        "period_week": week_number,
        "period_month": created_at.month,
        "period_year": created_at.year,
        "created_at": created_at,
        "updated_at": created_at,
    }

    if row:
        for field, value in payload.items():
            setattr(row, field, value)
    else:
        row = FeedbackResponse(**payload)
        db.add(row)
        db.flush()
    return row


def run():
    db = SessionLocal()
    try:
        results = []
        for scenario in SCENARIOS:
            employee_id = scenario["employee_id"]
            receiver = db.query(Employee).filter_by(id=employee_id).first()
            if not receiver:
                raise RuntimeError(f"Employee {employee_id} not found")

            for entry in scenario["entries"]:
                sender = db.query(Employee).filter_by(id=entry["sender_id"]).first()
                if not sender:
                    raise RuntimeError(f"Sender {entry['sender_id']} not found")

                direction = FeedbackService._resolve_direction(entry["sender_role"], receiver.user.role)
                question = upsert_question(
                    db,
                    week_number=entry["week_number"],
                    direction=direction,
                    category=entry["category"],
                    department_id=receiver.department_id,
                    question_text=entry["question_text"],
                )
                row = upsert_response(
                    db,
                    sender_id=entry["sender_id"],
                    receiver_id=employee_id,
                    question_id=question.id,
                    response_text=entry["response_text"],
                    scores=entry["scores"],
                    created_at=entry["created_at"],
                    week_number=entry["week_number"],
                )

                analysis_payload, provider, model_name = AIService.analyze_weekly_feedback(
                    dept_name=receiver.department.name if receiver.department else "Genel",
                    target_role=receiver.user.role,
                    week_theme=entry["category"],
                    direction_label_tr=direction_label(direction),
                    question_text=question.question_text,
                    response_text=row.response_text,
                    score_communication=float(row.score_communication),
                    score_teamwork=float(row.score_teamwork),
                    score_leadership=float(row.score_leadership),
                    score_technical=float(row.score_technical),
                )

                analysis = NLPService.save_weekly_analysis(
                    db,
                    feedback_response=row,
                    analysis_payload=analysis_payload,
                    analysis_version="scenario-v1",
                    model_provider=provider,
                    model_name=model_name,
                )
                analysis.created_at = entry["created_at"]
                analysis.updated_at = entry["created_at"]

                memory = RAGService.upsert_weekly_feedback_memory(
                    db,
                    feedback_response=row,
                    analysis_payload=analysis_payload,
                )
                memory.created_at = entry["created_at"]
                memory.updated_at = entry["created_at"]

                row.created_at = entry["created_at"]
                row.updated_at = entry["created_at"]

                results.append(
                    {
                        "employee_id": employee_id,
                        "employee_name": scenario["employee_name"],
                        "week": entry["week_number"],
                        "provider": provider,
                        "model_name": model_name,
                        "sentiment_label": analysis_payload.get("sentiment_label"),
                        "motivation_score": analysis_payload.get("motivation_score"),
                        "burnout_risk": analysis_payload.get("burnout_risk"),
                        "flight_risk": analysis_payload.get("flight_risk"),
                        "flight_risk_score": analysis_payload.get("flight_risk_score"),
                        "complaint_topics": analysis_payload.get("complaint_topics"),
                        "praise_topics": analysis_payload.get("praise_topics"),
                        "manager_summary": analysis_payload.get("manager_summary"),
                    }
                )

            for week_number in (1, 2, 3):
                NLPService.rebuild_employee_profile(
                    db,
                    employee_id=employee_id,
                    period_type=NLPPeriodType.weekly,
                    period_year=2026,
                    period_month=3,
                    period_week=week_number,
                )
            NLPService.rebuild_employee_profile(
                db,
                employee_id=employee_id,
                period_type=NLPPeriodType.monthly,
                period_year=2026,
                period_month=3,
                period_week=None,
            )

        db.commit()

        print("=== WEEKLY ANALYSIS SNAPSHOT ===")
        for item in results:
            print(item)

        print("\n=== MONTHLY DEEP ANALYSIS ===")
        for employee_id in (79, 81, 82):
            print(NLPService.build_employee_monthly_deep_analysis(db, employee_id=employee_id, period_year=2026, period_month=3))

        print("\n=== MONTHLY RAG REPORT ===")
        for employee_id in (79, 81, 82):
            print(NLPService.build_employee_monthly_rag_report(db, employee_id=employee_id, period_year=2026, period_month=3))

    finally:
        db.close()


if __name__ == "__main__":
    run()
