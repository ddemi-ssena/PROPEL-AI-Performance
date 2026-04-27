from __future__ import annotations

from datetime import date, timedelta
import random

from app.core.security import get_password_hash
from app.db.models import Base
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackDirection, FeedbackQuestion
from app.db.models.kpi import KPI, KPIRecord, KPIUnit
from app.db.models.survey_response import SurveyResponse
from app.db.models.user import User, UserRole
from app.db.session import SessionLocal


db = SessionLocal()
RNG = random.Random(42)
SOFTWARE_DEPARTMENT_NAME = "Yazilim"


EMPLOYEE_SPECS = [
    {"code": "SE-001", "name": "Canan Dagdelen", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 6.2},
    {"code": "SE-002", "name": "Berkant Demir", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 3.8},
    {"code": "SE-003", "name": "Elif Ozturk", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 4.1},
    {"code": "SE-004", "name": "Murat Kaya", "team": "Backend", "position": "Lead Backend Engineer", "experience_years": 8.7},
    {"code": "SE-005", "name": "Selin Yilmaz", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 5.5},
    {"code": "SE-006", "name": "Caner Yildiz", "team": "Backend", "position": "Junior Backend Engineer", "experience_years": 1.4},
    {"code": "SE-007", "name": "Zeynep Celik", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 7.1},
    {"code": "SE-008", "name": "Burak Sahin", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 3.2},
    {"code": "SE-009", "name": "Emre Kilic", "team": "Backend", "position": "Junior Backend Engineer", "experience_years": 1.1},
    {"code": "SE-010", "name": "Gamze Arslan", "team": "Frontend", "position": "Senior Frontend Engineer", "experience_years": 6.0},
    {"code": "SE-011", "name": "Onur Polat", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 3.6},
    {"code": "SE-012", "name": "Derya Koc", "team": "Frontend", "position": "Lead Frontend Engineer", "experience_years": 8.2},
    {"code": "SE-013", "name": "Alper Sen", "team": "Frontend", "position": "Junior Frontend Engineer", "experience_years": 1.0},
    {"code": "SE-014", "name": "Irem Acar", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 2.9},
    {"code": "SE-015", "name": "Merve Tetik", "team": "Frontend", "position": "Senior Frontend Engineer", "experience_years": 5.8},
    {"code": "SE-016", "name": "Cenk Uysal", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 4.0},
    {"code": "SE-017", "name": "Ece Ozkan", "team": "Frontend", "position": "Senior Frontend Engineer", "experience_years": 6.4},
    {"code": "SE-018", "name": "Ozan Gunes", "team": "Frontend", "position": "Junior Frontend Engineer", "experience_years": 1.7},
    {"code": "SE-019", "name": "Tolga Erdem", "team": "DevOps", "position": "Lead DevOps Engineer", "experience_years": 9.0},
    {"code": "SE-020", "name": "Pinar Aksoy", "team": "DevOps", "position": "Senior DevOps Engineer", "experience_years": 5.9},
    {"code": "SE-021", "name": "Kerem Tunc", "team": "DevOps", "position": "Mid DevOps Engineer", "experience_years": 3.5},
    {"code": "SE-022", "name": "Sude Karaca", "team": "DevOps", "position": "Mid DevOps Engineer", "experience_years": 2.8},
    {"code": "SE-023", "name": "Baris Eren", "team": "DevOps", "position": "Junior DevOps Engineer", "experience_years": 1.3},
    {"code": "SE-024", "name": "Melis Vural", "team": "DevOps", "position": "Mid DevOps Engineer", "experience_years": 4.2},
    {"code": "SE-025", "name": "Yigit Ari", "team": "DevOps", "position": "Senior DevOps Engineer", "experience_years": 6.7},
    {"code": "SE-026", "name": "Asli Cetin", "team": "QA", "position": "Lead QA Engineer", "experience_years": 8.5},
    {"code": "SE-027", "name": "Deniz Soylu", "team": "QA", "position": "Senior QA Engineer", "experience_years": 5.4},
    {"code": "SE-028", "name": "Burcu Isik", "team": "QA", "position": "Mid QA Engineer", "experience_years": 3.1},
    {"code": "SE-029", "name": "Kaan Oz", "team": "QA", "position": "Junior QA Engineer", "experience_years": 1.2},
    {"code": "SE-030", "name": "Naz Yalin", "team": "QA", "position": "Mid QA Engineer", "experience_years": 2.6},
]


KPI_DEFINITIONS = [
    ("KPI-1 GTO", "Gorev Tamamlama Orani", "Sprint taahhut yerine getirme seviyesi", KPIUnit.percentage, 88),
    ("KPI-2 ZTO", "Zamaninda Teslim Orani", "Planlanan teslimlerin zamaninda bitme orani", KPIUnit.percentage, 90),
    ("KPI-3 GKE", "Goreli Katki Endeksi", "Kisiye gore normalize edilmis uretim katki skoru", KPIUnit.numeric, 75),
    ("KPI-4 KKKE", "Kod Katki Kalite Endeksi", "Kod kalitesi ve surdurulebilirlik dengesi", KPIUnit.numeric, 82),
    ("KPI-5 BY", "Bug Yogunlugu", "Kod kalitesini etkileyen bug yogunlugu", KPIUnit.numeric, 18),
    ("KPI-6 KBO", "Kritik Bug Orani", "Kritik bug yuzdesi", KPIUnit.percentage, 12),
    ("KPI-7 CKO", "Code Review Kabul Orani", "Code review kabul verimliligi", KPIUnit.percentage, 85),
    ("KPI-8 ODS", "Ortalama PR Duzeltme Sayisi", "PR basina ortalama duzeltme sayisi", KPIUnit.numeric, 2.5),
    ("KPI-9 IYE", "Is Yuku Endeksi", "Is yukunun dengeli tasinma seviyesi", KPIUnit.numeric, 65),
    ("KPI-10 SAYS", "Surekli Asiri Yuk Skoru", "Tukenmislik riski gostergesi", KPIUnit.numeric, 25),
    ("KPI-11 TYO", "Toplanti Yuku Orani", "Toplanti yogunlugunun is akisina etkisi", KPIUnit.percentage, 20),
    ("KPI-12 EKS", "Ekip Katki Skoru", "Review, mentorluk ve destek kalitesi", KPIUnit.numeric, 78),
    ("KPI-13 360-GBS", "360 Geri Bildirim Skoru", "Yonetsel ve ekip geri bildirim ortalamasi", KPIUnit.numeric, 80),
    ("KPI-14 OMS", "Organizasyonel Merkezilik Skoru", "Ag icindeki etkilesim ve kritik rol seviyesi", KPIUnit.numeric, 70),
    ("KPI-15 MS", "Motivasyon Skoru", "Calisan motivasyon seviyesi", KPIUnit.numeric, 78),
    ("KPI-16 MTE", "Motivasyon Trend Egimi", "Motivasyondaki artis-azalis egimi", KPIUnit.numeric, 0.15),
    ("KPI-17 GKS", "Gelisim Katilim Skoru", "Egitim ve gelisim etkinliklerine katilim", KPIUnit.numeric, 72),
    ("KPI-18 GPS", "Genel Performans Skoru", "Birlesik performans skoru", KPIUnit.numeric, 80),
    ("KPI-19 ARS", "Ayrilma Riski Skoru", "Erken uyari attrition skoru", KPIUnit.numeric, 30),
    ("KPI-20 PPE", "Potansiyel Performans Endeksi", "Yuksek potansiyel gostergesi", KPIUnit.numeric, 76),
]


TEAM_LOAD_FACTOR = {
    "Backend": 1.00,
    "Frontend": 0.98,
    "DevOps": 1.08,
    "QA": 0.93,
}

ROLE_FACTOR = {
    "Junior": 0.86,
    "Mid": 1.00,
    "Senior": 1.10,
    "Lead": 1.18,
}

TEAM_MEETING_FACTOR = {
    "Backend": 0.95,
    "Frontend": 1.05,
    "DevOps": 1.15,
    "QA": 1.02,
}


def clamp(value: float, lower: float, upper: float, digits: int = 2) -> float:
    return round(max(lower, min(upper, value)), digits)


def get_role_bucket(position: str) -> str:
    return position.split(" ", 1)[0]


def clear_all_data() -> None:
    """Tum verileri tablo bagimlilik sirasi ile temizle."""
    print("Mevcut veriler temizleniyor...")
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    print("Veriler temizlendi.")


def create_users() -> list[User]:
    print("Kullanicilar olusturuluyor...")
    users = [
        User(
            email="admin@propel.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin Kullanici",
            role=UserRole.admin,
            is_active=True,
        ),
        User(
            email="manager.yazilim@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Ahmet Yilmaz",
            role=UserRole.department_manager,
            is_active=True,
        ),
    ]

    for spec in EMPLOYEE_SPECS:
        users.append(
            User(
                email=f"{spec['code'].lower()}@propel.com",
                hashed_password=get_password_hash("employee123"),
                full_name=spec["name"],
                role=UserRole.employee,
                is_active=True,
            )
        )

    db.add_all(users)
    db.commit()
    print(f"{len(users)} kullanici olusturuldu.")
    return users


def create_departments() -> list[Department]:
    print("Departmanlar olusturuluyor...")
    departments = [
        Department(
            name=SOFTWARE_DEPARTMENT_NAME,
            description="Backend, Frontend, DevOps ve QA takimlarini kapsayan yazilim organizasyonu",
        )
    ]
    db.add_all(departments)
    db.commit()
    print(f"{len(departments)} departman olusturuldu.")
    return departments


def create_employees(users: list[User], departments: list[Department]) -> list[Employee]:
    print("Calisanlar olusturuluyor...")
    user_map = {user.email: user for user in users}
    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)

    employees = [
        Employee(
            user_id=user_map["manager.yazilim@propel.com"].id,
            department_id=software_department.id,
            external_employee_code="MGR-001",
            team="Yonetim",
            position="Yazilim Departman Muduru",
            experience_years=12.0,
            hire_date=date(2021, 1, 11),
        )
    ]

    for index, spec in enumerate(EMPLOYEE_SPECS, start=1):
        email = f"{spec['code'].lower()}@propel.com"
        employees.append(
            Employee(
                user_id=user_map[email].id,
                department_id=software_department.id,
                external_employee_code=spec["code"],
                team=spec["team"],
                position=spec["position"],
                experience_years=spec["experience_years"],
                hire_date=date(2022, 1, 3) + timedelta(days=index * 29),
            )
        )

    db.add_all(employees)
    db.commit()
    print(f"{len(employees)} employee kaydi olusturuldu.")
    return employees


def create_kpis(departments: list[Department]):
    print("KPI tanimlari olusturuluyor...")
    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)

    kpis = [
        KPI(
            name=title,
            description=f"{code} | {description}",
            unit=unit,
            department_id=software_department.id,
            target_value=target_value,
        )
        for code, title, description, unit, target_value in KPI_DEFINITIONS
    ]
    db.add_all(kpis)
    db.commit()

    for kpi in kpis:
        db.refresh(kpi)

    kpi_map = {
        code: kpi.id
        for (code, _, _, _, _), kpi in zip(KPI_DEFINITIONS, kpis)
    }
    print(f"{len(kpis)} KPI tanimi olusturuldu.")
    return kpis, kpi_map


def generate_kpi_values(employee: Employee, month_offset: int) -> dict[str, float]:
    role_bucket = get_role_bucket(employee.position or "Mid")
    role_factor = ROLE_FACTOR.get(role_bucket, 1.0)
    team_factor = TEAM_LOAD_FACTOR.get(employee.team or "Backend", 1.0)
    meeting_factor = TEAM_MEETING_FACTOR.get(employee.team or "Backend", 1.0)
    seasonality = 1 + ((month_offset % 3) - 1) * 0.03
    noise = lambda scale: RNG.uniform(-scale, scale)

    gto = clamp(74 + role_factor * 12 + noise(4), 55, 100)
    zto = clamp(gto - 3 + noise(3), 50, 100)
    gke = clamp(58 + role_factor * 18 * team_factor * seasonality + noise(5), 35, 100)
    kkke = clamp(62 + role_factor * 14 - noise(4), 40, 100)
    bug_yogunlugu = clamp(32 - role_factor * 8 + noise(4), 6, 45)
    kritik_bug = clamp(20 - role_factor * 5 + noise(3), 2, 30)
    cko = clamp(68 + role_factor * 16 + noise(5), 45, 100)
    ods = clamp(4.2 - role_factor * 1.2 + noise(0.6), 0.5, 6.0)
    iye = clamp(48 + team_factor * 18 + noise(5), 25, 100)
    says = clamp(18 + team_factor * 9 + (iye - 60) * 0.35 + noise(4), 5, 100)
    tyo = clamp(14 + meeting_factor * 8 + noise(3), 6, 45)
    eks = clamp(52 + role_factor * 20 + noise(4), 35, 100)
    gbs = clamp(58 + role_factor * 18 + noise(5), 40, 100)
    oms = clamp(45 + role_factor * 18 + noise(6), 20, 100)
    ms = clamp(72 + role_factor * 8 - (says - 25) * 0.35 + noise(5), 35, 100)
    mte = clamp(((ms - 70) / 100) + noise(0.08), -1.0, 1.0)
    gks = clamp(48 + role_factor * 16 + noise(6), 20, 100)
    gps = clamp((gto * 0.18) + (kkke * 0.16) + (eks * 0.14) + (gbs * 0.14) + (ms * 0.18) - (bug_yogunlugu * 0.12), 30, 100)
    ars = clamp(72 - ms * 0.45 + says * 0.35 + kritik_bug * 0.20 + noise(5), 5, 100)
    ppe = clamp((gps * 0.45) + (gks * 0.25) + (oms * 0.15) + (ms * 0.15), 30, 100)

    return {
        "KPI-1 GTO": gto,
        "KPI-2 ZTO": zto,
        "KPI-3 GKE": gke,
        "KPI-4 KKKE": kkke,
        "KPI-5 BY": bug_yogunlugu,
        "KPI-6 KBO": kritik_bug,
        "KPI-7 CKO": cko,
        "KPI-8 ODS": ods,
        "KPI-9 IYE": iye,
        "KPI-10 SAYS": says,
        "KPI-11 TYO": tyo,
        "KPI-12 EKS": eks,
        "KPI-13 360-GBS": gbs,
        "KPI-14 OMS": oms,
        "KPI-15 MS": ms,
        "KPI-16 MTE": mte,
        "KPI-17 GKS": gks,
        "KPI-18 GPS": gps,
        "KPI-19 ARS": ars,
        "KPI-20 PPE": ppe,
    }


def create_kpi_records(employees: list[Employee], kpi_map: dict[str, int]) -> list[KPIRecord]:
    print("KPI kayitlari olusturuluyor...")
    records: list[KPIRecord] = []
    today = date.today()
    software_employees = [employee for employee in employees if employee.team != "Yonetim"]

    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        for employee in software_employees:
            values = generate_kpi_values(employee, month_offset)
            for kpi_name, value in values.items():
                records.append(
                    KPIRecord(
                        kpi_id=kpi_map[kpi_name],
                        employee_id=employee.id,
                        value=value,
                        period_date=period_date,
                    )
                )

    db.add_all(records)
    db.commit()
    print(f"{len(records)} KPI kaydi olusturuldu.")
    return records


def create_survey_responses(employees: list[Employee]) -> list[SurveyResponse]:
    print("Anket cevaplari olusturuluyor...")
    responses: list[SurveyResponse] = []
    today = date.today()
    software_employees = [employee for employee in employees if employee.team != "Yonetim"]

    for week_offset in range(8):
        period_date = today - timedelta(days=7 * week_offset)
        for employee in software_employees:
            role_bucket = get_role_bucket(employee.position or "Mid")
            role_factor = ROLE_FACTOR.get(role_bucket, 1.0)
            workload = TEAM_LOAD_FACTOR.get(employee.team or "Backend", 1.0)
            pulse_score = clamp(3.2 + (role_factor - 0.9) * 0.7 - (workload - 1.0) * 0.6 + RNG.uniform(-0.4, 0.4), 1.8, 5.0, 1)
            mte_score = clamp((pulse_score - 3.4) * 0.35 + RNG.uniform(-0.08, 0.08), -1.0, 1.0)
            ars_score = clamp(0.55 - ((pulse_score - 3.0) * 0.22) + (workload - 1.0) * 0.18 + RNG.uniform(-0.05, 0.05), 0.05, 0.95)
            responses.append(
                SurveyResponse(
                    employee_id=employee.id,
                    survey_type="weekly_pulse",
                    score=pulse_score,
                    period_date=period_date,
                    comments=f"{employee.team} ekibinde haftalik nabiz kaydi",
                    raw_data={
                        "team": employee.team,
                        "focus": "delivery" if employee.team in {"Backend", "Frontend"} else "stability",
                        "energy_signal": "stable" if pulse_score >= 3.5 else "watch",
                    },
                    mte_score=mte_score,
                    ars_score=ars_score,
                )
            )

    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        for employee in software_employees:
            base = clamp(3.3 + RNG.uniform(-0.5, 0.6), 2.0, 5.0, 1)
            responses.extend(
                [
                    SurveyResponse(employee_id=employee.id, survey_type="motivation", score=base, period_date=period_date, comments=None),
                    SurveyResponse(employee_id=employee.id, survey_type="satisfaction", score=clamp(base + RNG.uniform(-0.3, 0.4), 2.0, 5.0, 1), period_date=period_date, comments=None),
                    SurveyResponse(employee_id=employee.id, survey_type="stress", score=clamp(5.1 - base + RNG.uniform(-0.3, 0.3), 1.5, 5.0, 1), period_date=period_date, comments=None),
                ]
            )

    db.add_all(responses)
    db.commit()
    print(f"{len(responses)} anket cevabi olusturuldu.")
    return responses


def create_feedback_questions(departments: list[Department]) -> list[FeedbackQuestion]:
    print("Haftalik feedback sorulari olusturuluyor...")
    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)

    questions = [
        FeedbackQuestion(
            week_number=1,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu hafta birlikte calisma akisinda en somut katkisi neydi?",
            category="Takim Calismasi",
            department_id=software_department.id,
        ),
        FeedbackQuestion(
            week_number=2,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Kod kalitesi, teslimat disiplini veya destek davranisi acisindan ne gozlemledin?",
            category="Teslimat ve Kalite",
            department_id=software_department.id,
        ),
        FeedbackQuestion(
            week_number=3,
            direction=FeedbackDirection.manager_to_employee,
            question_text="Bu hafta onceliklendirme, risk takibi ve blokaj yonetiminde nasil bir etki yaratti?",
            category="Yonetici Gozlemi",
            department_id=software_department.id,
        ),
        FeedbackQuestion(
            week_number=4,
            direction=FeedbackDirection.employee_to_manager,
            question_text="Bu ay yonetsel destek, teknik mentorluk ve surec netligi acisindan neler iyi gitti?",
            category="Yonetsel Destek",
            department_id=software_department.id,
        ),
    ]

    db.add_all(questions)
    db.commit()
    print(f"{len(questions)} feedback sorusu olusturuldu.")
    return questions


def main() -> None:
    print("Software analytics seed baslatiliyor...\n")
    clear_all_data()
    users = create_users()
    departments = create_departments()
    employees = create_employees(users, departments)
    kpis, kpi_map = create_kpis(departments)
    kpi_records = create_kpi_records(employees, kpi_map)
    survey_responses = create_survey_responses(employees)
    feedback_questions = create_feedback_questions(departments)

    print("\nSeed tamamlandi!")
    print(
        f"- {len(users)} kullanici\n"
        f"- {len(departments)} departman\n"
        f"- {len(employees)} employee\n"
        f"- {len(kpis)} KPI tanimi\n"
        f"- {len(kpi_records)} KPI kaydi\n"
        f"- {len(survey_responses)} anket cevabi\n"
        f"- {len(feedback_questions)} feedback sorusu"
    )
    print("\nTest hesaplari:")
    print("Admin: admin@propel.com / admin123")
    print("Yazilim Manager: manager.yazilim@propel.com / manager123")
    print("Ornek Calisan: se001@propel.com / employee123")


if __name__ == "__main__":
    main()
    db.close()
