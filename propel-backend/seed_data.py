from __future__ import annotations

from datetime import date, datetime, timedelta
import random

from app.core.security import get_password_hash
from app.db.models import Base
from app.db.models.data_upload import DataUpload
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import FeedbackDirection, FeedbackQuestion, FeedbackResponse
from app.db.models.kpi import KPI, KPIRecord, KPIUnit
from app.db.models.survey_response import SurveyResponse
from app.db.models.user import User, UserRole
from app.db.session import SessionLocal
from app.services.ai_service import AIService
from app.services.nlp_service import NLPService
from app.services.rag_service import RAGService


db = SessionLocal()
RNG = random.Random(42)
SOFTWARE_DEPARTMENT_NAME = "YazÄ±lÄ±m GeliÅŸtirme"
SALES_DEPARTMENT_NAME = "SatÄ±ÅŸ"


EMPLOYEE_SPECS = [
    # v8 software dataset employee_id listesiyle birebir eslesir.
    {"code": "SE-001", "name": "Canan Dagdelen", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 3.8},
    {"code": "SE-004", "name": "Berkant Demir", "team": "DevOps", "position": "Mid DevOps Engineer", "experience_years": 3.5},
    {"code": "SE-005", "name": "Elif Ozturk", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 4.1},
    {"code": "SE-006", "name": "Murat Kaya", "team": "Frontend", "position": "Junior Frontend Engineer", "experience_years": 1.0},
    {"code": "SE-007", "name": "Selin Yilmaz", "team": "QA", "position": "Mid QA Engineer", "experience_years": 3.1},
    {"code": "SE-009", "name": "Caner Yildiz", "team": "Backend", "position": "Mid Backend Engineer", "experience_years": 3.2},
    {"code": "SE-010", "name": "Zeynep Celik", "team": "Frontend", "position": "Junior Frontend Engineer", "experience_years": 1.4},
    {"code": "SE-013", "name": "Burak Sahin", "team": "Backend", "position": "Junior Backend Engineer", "experience_years": 1.1},
    {"code": "SE-014", "name": "Emre Kilic", "team": "Frontend", "position": "Senior Frontend Engineer", "experience_years": 6.0},
    {"code": "SE-016", "name": "Gamze Arslan", "team": "DevOps", "position": "Junior DevOps Engineer", "experience_years": 1.3},
    {"code": "SE-017", "name": "Onur Polat", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 6.2},
    {"code": "SE-018", "name": "Derya Koc", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 3.6},
    {"code": "SE-020", "name": "Alper Sen", "team": "DevOps", "position": "Senior DevOps Engineer", "experience_years": 5.9},
    {"code": "SE-025", "name": "Irem Acar", "team": "Backend", "position": "Lead Backend Engineer", "experience_years": 8.7},
    {"code": "SE-026", "name": "Merve Tetik", "team": "Frontend", "position": "Junior Frontend Engineer", "experience_years": 1.7},
    {"code": "SE-027", "name": "Cenk Uysal", "team": "QA", "position": "Junior QA Engineer", "experience_years": 1.2},
    {"code": "SE-028", "name": "Ece Ozkan", "team": "DevOps", "position": "Mid DevOps Engineer", "experience_years": 4.0},
    {"code": "SE-031", "name": "Ozan Gunes", "team": "QA", "position": "Mid QA Engineer", "experience_years": 2.6},
    {"code": "SE-032", "name": "Tolga Erdem", "team": "DevOps", "position": "Lead DevOps Engineer", "experience_years": 9.0},
    {"code": "SE-033", "name": "Pinar Aksoy", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 5.5},
    {"code": "SE-034", "name": "Kerem Tunc", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 2.9},
    {"code": "SE-035", "name": "Sude Karaca", "team": "QA", "position": "Senior QA Engineer", "experience_years": 5.4},
    {"code": "SE-038", "name": "Baris Eren", "team": "Frontend", "position": "Mid Frontend Engineer", "experience_years": 4.0},
    {"code": "SE-040", "name": "Melis Vural", "team": "DevOps", "position": "Senior DevOps Engineer", "experience_years": 6.7},
    {"code": "SE-042", "name": "Yigit Ari", "team": "Frontend", "position": "Lead Frontend Engineer", "experience_years": 8.2},
    {"code": "SE-045", "name": "Asli Cetin", "team": "Backend", "position": "Lead Backend Engineer", "experience_years": 8.5},
    {"code": "SE-046", "name": "Deniz Soylu", "team": "Frontend", "position": "Senior Frontend Engineer", "experience_years": 5.8},
    {"code": "SE-047", "name": "Burcu Isik", "team": "QA", "position": "Mid QA Engineer", "experience_years": 3.1},
    {"code": "SE-048", "name": "Kaan Oz", "team": "DevOps", "position": "Senior DevOps Engineer", "experience_years": 6.4},
    {"code": "SE-049", "name": "Naz Yalin", "team": "Backend", "position": "Senior Backend Engineer", "experience_years": 7.1},
]

SALES_EMPLOYEE_SPECS = [
    # TakÄ±m isimleri Excel'deki Region sÃ¼tunuyla birebir eÅŸleÅŸiyor
    {"code": "SA-001", "name": "Ali YÄ±lmaz",      "team": "Marmara",           "position": "Senior Sales Representative", "experience_years": 7.5},
    {"code": "SA-002", "name": "AyÅŸe Demir",      "team": "Ege",               "position": "Junior Sales Representative", "experience_years": 1.2},
    {"code": "SA-003", "name": "Mehmet Kaya",      "team": "Karadeniz",         "position": "Sales Team Lead",             "experience_years": 9.1},
    {"code": "SA-004", "name": "Fatma Ã‡elik",      "team": "Marmara",           "position": "Mid Sales Representative",    "experience_years": 2.6},
    {"code": "SA-005", "name": "Mustafa KoÃ§",      "team": "Karadeniz",         "position": "Sales Team Lead",             "experience_years": 8.3},
    {"code": "SA-006", "name": "Zeynep Åahin",     "team": "Dogu Anadolu",      "position": "Sales Team Lead",             "experience_years": 8.8},
    {"code": "SA-007", "name": "Ahmet Ã–ztÃ¼rk",     "team": "Ic Anadolu",        "position": "Senior Sales Representative", "experience_years": 4.2},
    {"code": "SA-008", "name": "Elif AydÄ±n",       "team": "Marmara",           "position": "Mid Sales Representative",    "experience_years": 2.4},
    {"code": "SA-009", "name": "Caner YÄ±ldÄ±z",     "team": "Akdeniz",           "position": "Mid Sales Representative",    "experience_years": 2.7},
    {"code": "SA-010", "name": "Burcu Arslan",      "team": "Akdeniz",           "position": "Junior Sales Representative", "experience_years": 1.1},
    # SA-011: satis.employee@propel.com â€” Zeynep Kaya
    {"code": "SA-011", "name": "Zeynep Kaya",      "team": "Akdeniz",           "position": "Senior Sales Executive",      "experience_years": 4.3},
    {"code": "SA-012", "name": "Kerem Arslan",      "team": "Guneydogu Anadolu", "position": "Sales Team Lead",             "experience_years": 5.7},
    {"code": "SA-013", "name": "Selin YÄ±lmaz",     "team": "Ic Anadolu",        "position": "Sales Team Lead",             "experience_years": 8.6},
    {"code": "SA-014", "name": "Tuncay DoÄŸan",     "team": "Dogu Anadolu",      "position": "Senior Sales Representative", "experience_years": 3.8},
    {"code": "SA-015", "name": "Nihan Korkmaz",     "team": "Dogu Anadolu",      "position": "Junior Sales Representative", "experience_years": 1.0},
    {"code": "SA-016", "name": "Baran Ã–zdemir",    "team": "Guneydogu Anadolu", "position": "Junior Sales Representative", "experience_years": 1.3},
    {"code": "SA-017", "name": "Derya Kaplan",      "team": "Guneydogu Anadolu", "position": "Sales Team Lead",             "experience_years": 5.3},
    {"code": "SA-018", "name": "Serhat Bulut",      "team": "Dogu Anadolu",      "position": "Senior Sales Representative", "experience_years": 3.7},
    {"code": "SA-019", "name": "Merve Polat",       "team": "Akdeniz",           "position": "Senior Sales Representative", "experience_years": 4.1},
    {"code": "SA-020", "name": "Ozan Ã‡etin",       "team": "Dogu Anadolu",      "position": "Junior Sales Representative", "experience_years": 1.2},
    {"code": "SA-021", "name": "Gamze Kurt",        "team": "Ege",               "position": "Mid Sales Representative",    "experience_years": 2.8},
    {"code": "SA-022", "name": "Hakan Acar",        "team": "Ic Anadolu",        "position": "Sales Team Lead",             "experience_years": 9.2},
    {"code": "SA-023", "name": "Rana ÅimÅŸek",      "team": "Akdeniz",           "position": "Junior Sales Representative", "experience_years": 1.0},
    {"code": "SA-024", "name": "Emre YÄ±ldÄ±z",      "team": "Marmara",           "position": "Senior Sales Representative", "experience_years": 3.9},
    {"code": "SA-025", "name": "PÄ±nar GÃ¼l",        "team": "Marmara",           "position": "Sales Team Lead",             "experience_years": 8.8},
    {"code": "SA-026", "name": "Tolga Kara",        "team": "Akdeniz",           "position": "Sales Team Lead",             "experience_years": 5.5},
    {"code": "SA-027", "name": "AslÄ± ErdoÄŸan",     "team": "Dogu Anadolu",      "position": "Mid Sales Representative",    "experience_years": 2.4},
    {"code": "SA-028", "name": "Volkan Åahin",     "team": "Ege",               "position": "Sales Team Lead",             "experience_years": 8.2},
    {"code": "SA-029", "name": "Ä°rem Ã–zkan",       "team": "Dogu Anadolu",      "position": "Sales Team Lead",             "experience_years": 5.8},
    {"code": "SA-030", "name": "Burak Ã‡alÄ±ÅŸkan",   "team": "Ic Anadolu",        "position": "Mid Sales Representative",    "experience_years": 2.9},
]


KPI_DEFINITIONS = [
    ("KPI-1 GTO", "Gorev Tamamlama Orani", "Sprint taahhut yerine getirme seviyesi", KPIUnit.percentage, 88),
    ("KPI-2 ZTO", "Zamaninda Teslim Orani", "Planlanan teslimlerin zamaninda bitme orani", KPIUnit.percentage, 90),
    ("KPI-3 GKE", "Goreli Katki Endeksi", "Kisiye gore normalize edilmis uretim katki skoru", KPIUnit.numeric, 75),
    ("KPI-4 KKKE", "Kod Katki Kalite Endeksi", "Kod kalitesi ve surdurulebilirlik dengesi", KPIUnit.numeric, 82),
    ("KPI-5 BY", "Bug Yogunlugu", "Kod kalitesini etkileyen bug yogunlugu", KPIUnit.numeric, 18),
    ("KPI-6 KBO", "Kritik Bug Orani", "Kritik bug yuzdesi", KPIUnit.percentage, 12),
    ("KPI-7 CRKO", "Code Review Kabul Orani", "Code review kabul verimliligi", KPIUnit.percentage, 85),
    ("KPI-8 OPDS", "Ortalama PR Duzeltme Sayisi", "PR basina ortalama duzeltme sayisi", KPIUnit.numeric, 2.5),
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


SALES_KPI_DEFINITIONS = [
    ("KPI-S1 SHGO", "Satis Hedef Gerceklesme Orani", "Satis hedeflerinin gerceklesme orani", KPIUnit.percentage, 90),
    ("KPI-S2 SAY", "Satis Aktivite Yogunlugu", "Arama, toplanti ve demo sayilari bazli", KPIUnit.numeric, 80),
    ("KPI-S3 YMKO", "Yeni Musteri Kazanim Orani", "Portfoye eklenen yeni musteri orani", KPIUnit.percentage, 15),
    ("KPI-S4 LMDO", "Lead'den Musteriye Donusum Orani", "Sicak leadlerin satisa donme orani", KPIUnit.percentage, 25),
    ("KPI-S5 TKO", "Teklif Kazanma Orani", "Verilen tekliflerin onaylanma orani", KPIUnit.percentage, 40),
    ("KPI-S6 OSDS", "Ortalama Satis Dongu Suresi", "Ilk temastan kapanisa ortalama gun", KPIUnit.numeric, 30),
    ("KPI-S7 OSD", "Ortalama Satis Degeri", "Satislarin ortalama tutari (endeks)", KPIUnit.numeric, 75),
    ("KPI-S8 GKP", "Gelir Katki Payi", "Sirket hedefine edilen gelir katkisi", KPIUnit.percentage, 10),
    ("KPI-S9 UCO", "Upsell / Cross-sell Orani", "Mevcut musterilere ek satis orani", KPIUnit.percentage, 20),
    ("KPI-S10 PSO", "Pipeline Saglik Orani", "Satistaki firsatlarin ilerleme sagligi", KPIUnit.percentage, 85),
    ("KPI-S11 PYO", "Pipeline Yaslanma Orani", "Firsatlarin ortalama bekleme suresi", KPIUnit.percentage, 15),
    ("KPI-S12 SIYE", "Satis Is Yuku Endeksi", "Musteri ve operasyon yuku", KPIUnit.numeric, 75),
    ("KPI-S13 SSAYS", "Surekli Asiri Yuk Skoru", "Stres ve is yuku tukenmisligi", KPIUnit.numeric, 25),
    ("KPI-S14 TDO", "Takip Disiplini Orani", "Toplanti ve teklif follow-up duzeni", KPIUnit.percentage, 90),
    ("KPI-S15 MMS", "Musteri Memnuniyet Skoru", "Musteri geri bildirim ortalamasi", KPIUnit.numeric, 85),
    ("KPI-S16 SO", "Sikayet Orani", "Musterilerden gelen sikayet orani", KPIUnit.percentage, 5),
    ("KPI-S17 CRMKD", "CRM Kullanim Disiplini", "Veri girislerindeki eksiksizlik", KPIUnit.percentage, 88),
    ("KPI-S18 SEKS", "Satis Ekip Katki Skoru", "Ekiple tecrube/bilgi paylasimi", KPIUnit.numeric, 80),
    ("KPI-S19 360-SGBS", "360 Satis Geri Bildirim Skoru", "Ekip ve yoneticiden gelen geribildirim", KPIUnit.numeric, 80),
    ("KPI-S20 MS", "Motivasyon Skoru", "Calisan motivasyonu", KPIUnit.numeric, 75),
    ("KPI-S21 MTE", "Motivasyon Trend Egimi", "Aylik motivasyon artis veya dususu", KPIUnit.numeric, 0.1),
    ("KPI-S22 GKS", "Gelisim Katilim Skoru", "Egitim ve etkinlik katilimi", KPIUnit.numeric, 70),
    ("KPI-S23 SGPS", "Satis Genel Performans Skoru", "Genel satis performans ortalamasi", KPIUnit.numeric, 82),
    ("KPI-S24 SARS", "Satis Ayrilma Riski Skoru", "Calisanin isi birakma riski", KPIUnit.numeric, 25),
    ("KPI-S25 PSPE", "Potansiyel Satis Performans Endeksi", "Gelecek donem potansiyel tahmini", KPIUnit.numeric, 80),
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


def employee_login_email(spec: dict) -> str:
    if spec["code"] == "SE-001":
        return "developer1@propel.com"
    return f"{spec['code'].lower()}@propel.com"


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
            full_name="Admin KullanÄ±cÄ±",
            role=UserRole.admin,
            is_active=True,
        ),
        User(
            email="manager.yazilim@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Ahmet YÄ±lmaz",
            role=UserRole.department_manager,
            is_active=True,
        ),
        User(
            email="manager.satis@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Hatice YÄ±ldÄ±rÄ±m",
            role=UserRole.department_manager,
            is_active=True,
        ),
        User(
            email="satis.employee@propel.com",
            hashed_password=get_password_hash("satis123"),
            full_name="Zeynep Kaya",
            role=UserRole.employee,
            is_active=True,
        ),
    ]

    for spec in EMPLOYEE_SPECS:
        login_email = employee_login_email(spec)
        login_password = "dev123" if spec["code"] == "SE-001" else "employee123"
        users.append(
            User(
                email=login_email,
                hashed_password=get_password_hash(login_password),
                full_name=spec["name"],
                role=UserRole.employee,
                is_active=True,
            )
        )

    for spec in SALES_EMPLOYEE_SPECS:
        if spec["code"] == "SA-011":
            continue  # SA-011 â†’ satis.employee@propel.com olarak ayrÄ±ca eklendi
        login_email = f"{spec['code'].lower()}@propel.com"
        login_password = "employee123"
        users.append(
            User(
                email=login_email,
                hashed_password=get_password_hash(login_password),
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
        ),
        Department(
            name=SALES_DEPARTMENT_NAME,
            description="Kurumsal Satis, Bireysel Satis ve Musteri Basarisi takimlarini kapsayan satis organizasyonu",
        )
    ]
    db.add_all(departments)
    db.commit()
    print(f"{len(departments)} departman olusturuldu.")
    return departments


def create_employees(users: list[User], departments: list[Department]) -> list[Employee]:
    print("Calisanlar olusturuluyor...")
    employees: list[Employee] = []
    user_map = {user.email: user for user in users}
    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)
    sales_department = next(dept for dept in departments if dept.name == SALES_DEPARTMENT_NAME)

    # Managerlar icin Employee kayitlari (Dashboardlarinin calismasi icin gerekli)
    employees.append(
        Employee(
            user_id=user_map["manager.yazilim@propel.com"].id,
            department_id=software_department.id,
            external_employee_code="MGR-SW",
            team="Yonetim",
            position="Software Department Manager",
            experience_years=12.0,
            hire_date=date(2020, 1, 1),
        )
    )
    employees.append(
        Employee(
            user_id=user_map["manager.satis@propel.com"].id,
            department_id=sales_department.id,
            external_employee_code="SA-031",
            team="Genel",
            position="Sales Department Manager",
            experience_years=12.0,
            hire_date=date(2019, 6, 1),
        )
    )

    # SA-011: satis.employee@propel.com â€” Zeynep Kaya
    employees.append(
        Employee(
            user_id=user_map["satis.employee@propel.com"].id,
            department_id=sales_department.id,
            external_employee_code="SA-011",
            team="Akdeniz",
            position="Senior Sales Executive",
            experience_years=4.3,
            hire_date=date(2021, 3, 15),
        )
    )

    for index, spec in enumerate(EMPLOYEE_SPECS, start=1):
        email = employee_login_email(spec)
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

    for index, spec in enumerate(SALES_EMPLOYEE_SPECS, start=1):
        if spec["code"] == "SA-011":
            continue  # SA-011 â†’ satis.employee@propel.com olarak ayrÄ±ca eklendi
        email = f"{spec['code'].lower()}@propel.com"
        employees.append(
            Employee(
                user_id=user_map[email].id,
                department_id=sales_department.id,
                external_employee_code=spec["code"],
                team=spec["team"],
                position=spec["position"],
                experience_years=spec["experience_years"],
                hire_date=date(2022, 6, 1) + timedelta(days=index * 15),
            )
        )

    db.add_all(employees)
    db.commit()
    print(f"{len(employees)} employee kaydi olusturuldu.")
    return employees


def create_kpis(departments: list[Department]):
    print("KPI tanimlari olusturuluyor...")
    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)
    sales_department = next(dept for dept in departments if dept.name == SALES_DEPARTMENT_NAME)

    kpis = []
    
    for code, title, description, unit, target_value in KPI_DEFINITIONS:
        kpis.append(KPI(
            name=title,
            description=f"{code} | {description}",
            unit=unit,
            department_id=software_department.id,
            target_value=target_value,
        ))

    for code, title, description, unit, target_value in SALES_KPI_DEFINITIONS:
        kpis.append(KPI(
            name=title,
            description=f"{code} | {description}",
            unit=unit,
            department_id=sales_department.id,
            target_value=target_value,
        ))

    db.add_all(kpis)
    db.commit()

    for kpi in kpis:
        db.refresh(kpi)

    kpi_map = {}
    for kpi in kpis:
        code = kpi.description.split(" | ")[0]
        kpi_map[code] = kpi.id

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
        "KPI-7 CRKO": cko,
        "KPI-8 OPDS": ods,
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


def generate_sales_kpi_values(employee: Employee, month_offset: int) -> dict[str, float]:
    role_bucket = get_role_bucket(employee.position or "Mid")
    role_factor = ROLE_FACTOR.get(role_bucket, 1.0)
    seasonality = 1 + ((month_offset % 4) - 1.5) * 0.05
    noise = lambda scale: RNG.uniform(-scale, scale)

    shgo = clamp(75 + role_factor * 15 * seasonality + noise(5), 50, 100)
    say = clamp(60 + role_factor * 20 + noise(6), 40, 100)
    ymko = clamp(10 + role_factor * 5 + noise(3), 2, 35)
    lmdo = clamp(15 + role_factor * 8 + noise(4), 5, 50)
    tko = clamp(25 + role_factor * 12 + noise(5), 10, 70)
    osds = clamp(45 - role_factor * 10 + noise(5), 15, 60)
    osd = clamp(60 + role_factor * 15 * seasonality + noise(5), 40, 100)
    gkp = clamp(8 + role_factor * 3 + noise(2), 2, 25)
    uco = clamp(12 + role_factor * 6 + noise(3), 5, 40)
    pso = clamp(70 + role_factor * 12 + noise(5), 50, 100)
    pyo = clamp(25 - role_factor * 5 + noise(4), 5, 45)
    siye = clamp(55 + role_factor * 15 + noise(6), 30, 100)
    ssays = clamp(15 + (siye - 60) * 0.4 + noise(5), 5, 80)
    tdo = clamp(75 + role_factor * 10 + noise(4), 50, 100)
    mms = clamp(78 + role_factor * 8 + noise(4), 60, 100)
    so = clamp(8 - role_factor * 2 + noise(2), 0, 20)
    crmkd = clamp(80 + role_factor * 5 + noise(4), 50, 100)
    seks = clamp(65 + role_factor * 15 + noise(5), 40, 100)
    gbs = clamp(70 + role_factor * 10 + noise(5), 50, 100)
    ms = clamp(75 + role_factor * 5 - (ssays - 20) * 0.3 + noise(5), 40, 100)
    mte = clamp(((ms - 75) / 100) + noise(0.08), -1.0, 1.0)
    gks = clamp(60 + role_factor * 12 + noise(5), 30, 100)
    sgps = clamp((shgo * 0.2) + (say * 0.1) + (lmdo * 0.15) + (mms * 0.15) + (gbs * 0.1) + (ms * 0.1) + (tdo * 0.1) + (pso * 0.1), 40, 100)
    sars = clamp(65 - ms * 0.4 + ssays * 0.3 + so * 1.5 + noise(5), 5, 100)
    pspe = clamp((sgps * 0.4) + (gks * 0.2) + (seks * 0.2) + (ms * 0.2), 40, 100)

    return {
        "KPI-S1 SHGO": shgo,
        "KPI-S2 SAY": say,
        "KPI-S3 YMKO": ymko,
        "KPI-S4 LMDO": lmdo,
        "KPI-S5 TKO": tko,
        "KPI-S6 OSDS": osds,
        "KPI-S7 OSD": osd,
        "KPI-S8 GKP": gkp,
        "KPI-S9 UCO": uco,
        "KPI-S10 PSO": pso,
        "KPI-S11 PYO": pyo,
        "KPI-S12 SIYE": siye,
        "KPI-S13 SSAYS": ssays,
        "KPI-S14 TDO": tdo,
        "KPI-S15 MMS": mms,
        "KPI-S16 SO": so,
        "KPI-S17 CRMKD": crmkd,
        "KPI-S18 SEKS": seks,
        "KPI-S19 360-SGBS": gbs,
        "KPI-S20 MS": ms,
        "KPI-S21 MTE": mte,
        "KPI-S22 GKS": gks,
        "KPI-S23 SGPS": sgps,
        "KPI-S24 SARS": sars,
        "KPI-S25 PSPE": pspe,
    }


def create_kpi_records(employees: list[Employee], kpi_map: dict[str, int]) -> list[KPIRecord]:
    print("KPI kayitlari olusturuluyor...")
    records: list[KPIRecord] = []
    today = date.today()
    employees_no_mgmt = [employee for employee in employees if employee.team != "Yonetim"]

    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        for employee in employees_no_mgmt:
            if employee.department and employee.department.name == SOFTWARE_DEPARTMENT_NAME:
                values = generate_kpi_values(employee, month_offset)
            else:
                values = generate_sales_kpi_values(employee, month_offset)
                
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
    employees_no_mgmt = [employee for employee in employees if employee.team != "Yonetim"]

    for week_offset in range(8):
        period_date = today - timedelta(days=7 * week_offset)
        for employee in employees_no_mgmt:
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
        for employee in employees_no_mgmt:
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
    sales_department = next(dept for dept in departments if dept.name == SALES_DEPARTMENT_NAME)

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
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu hafta ekip ici iletisim, yardimlasma ve sahiplenme davranisi nasil gorundu?",
            category="Iletisim ve Sahiplenme",
            department_id=software_department.id,
        ),
        FeedbackQuestion(
            week_number=4,
            direction=FeedbackDirection.employee_to_manager,
            question_text="Bu ay yonetsel destek, teknik mentorluk ve surec netligi acisindan neler iyi gitti?",
            category="Yonetsel Destek",
            department_id=software_department.id,
        ),
        FeedbackQuestion(
            week_number=1,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu hafta musteri gorusmelerinde veya takim ici paslasmalarda en buyuk katkisi neydi?",
            category="Musteri ve Takim Iletisimi",
            department_id=sales_department.id,
        ),
        FeedbackQuestion(
            week_number=2,
            direction=FeedbackDirection.peer_to_peer,
            question_text="CRM guncellemeleri, teklif takibi ve surec disiplininde nasil bir ornekti?",
            category="Surec ve Disiplin",
            department_id=sales_department.id,
        ),
        FeedbackQuestion(
            week_number=3,
            direction=FeedbackDirection.manager_to_employee,
            question_text="Bu hafta pipeline yonetimi, itiraz karsilama ve satis kapatma odakliligi nasildi?",
            category="Satis Odagi ve Yonetim",
            department_id=sales_department.id,
        ),
        FeedbackQuestion(
            week_number=4,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Zorlu musteri senaryolarinda veya hedeflere kosarken nasil bir durus sergiledi?",
            category="Stres Yonetimi ve Azim",
            department_id=sales_department.id,
        ),
        FeedbackQuestion(
            week_number=4,
            direction=FeedbackDirection.employee_to_manager,
            question_text="Bu ay kotalara ulasma konusunda yonetsel mentorluk ve saha destegi acisindan neler iyiydi?",
            category="Yonetsel Destek",
            department_id=sales_department.id,
        ),
    ]

    db.add_all(questions)
    db.commit()
    print(f"{len(questions)} feedback sorusu olusturuldu.")
    return questions


def get_feedback_anchor_dates() -> dict[int, date]:
    today = date.today()
    return {
        1: today.replace(day=3),
        2: today.replace(day=10),
        3: today.replace(day=17),
        4: today.replace(day=24),
    }


def get_feedback_question_map(questions: list[FeedbackQuestion]) -> dict[tuple[int, FeedbackDirection, int], FeedbackQuestion]:
    return {
        (question.week_number, question.direction, question.department_id): question
        for question in questions
    }


def classify_employee_signal(employee: Employee) -> str:
    code = employee.external_employee_code or ""
    if code in {"SE-003", "SE-009", "SE-023", "SE-029"}:
        return "watch"
    if code in {"SE-001", "SE-004", "SE-012", "SE-019", "SE-026"}:
        return "strong"
    return "steady"


def build_feedback_payload(employee: Employee, week_number: int, signal: str) -> tuple[str, tuple[int, int, int, int]]:
    team = employee.team or "ekip"
    role = get_role_bucket(employee.position or "Mid")

    if signal == "strong":
        text_map = {
            1: f"Bu hafta {team} akisinda blokaj gordugunde sakin kaldi ve cozum uretmek icin hizla sorumluluk aldi. Teknik kaliteyi korurken ekibin guvenini yuksek tuttu.",
            2: f"Teslimat ve kalite tarafinda {role.lower()} seviyesine uygun sekilde guven verdi. Kod duzeni, review disiplini ve takip konusunda istikrarli bir profil sergiledi.",
            3: f"Bu hafta hedefleri netlestirme, riskleri erken gorme ve onceliklendirme konusunda guclu bir etki yaratti. Takimi hizlandiran ve guven veren bir calisma bicimi vardi.",
            4: f"Ekip ici iletisimde acikti, yardim istendiginde hizli donus sagladi ve sahiplenme seviyesi yuksekti. Pozitif enerjisi takim uyumunu destekledi.",
        }
        score_map = {
            1: (5, 5, 4, 5),
            2: (4, 5, 4, 5),
            3: (4, 4, 5, 5),
            4: (5, 5, 4, 4),
        }
    elif signal == "watch":
        text_map = {
            1: f"Bu hafta {team} akisinda blokajlar uzadiginda kolay yoruldu ve sahiplenme seviyesi dalgalandi. Cozum ararken motivasyonunun hizla dustugu goruldu.",
            2: f"Teslimat ve kalite tarafinda dikkat daginikligi yasadi. Review yorumlarini uygulamakta ve isleri zamaninda kapatmakta zorlandigi anlar oldu.",
            3: f"Risk takibi ve onceliklendirme konusunda destege ihtiyac duydu. Belirsizlik anlarinda geri cekilme davranisi ekip uzerinde baski yaratti.",
            4: f"Iletisimde zaman zaman kapanik kaldi ve yardim istemeyi geciktirdi. Ekip uyumu gecen haftalara gore kirilgan gorundu.",
        }
        score_map = {
            1: (2, 2, 2, 2),
            2: (2, 2, 2, 3),
            3: (2, 2, 2, 2),
            4: (2, 2, 2, 2),
        }
    else:
        text_map = {
            1: f"Bu hafta {team} akisinda genel olarak sorumluluk aldi ancak bazi blokajlarda yonlendirmeye ihtiyac duydu. Geri bildirim aldiginda toparlanmaya acik bir tavir sergiledi.",
            2: f"Teslimat ve kalite dengesinde genelde istikrarliydi. Bazi detaylarda daha fazla kontrol gerekse de ekip icinde guven veren bir katkisi oldu.",
            3: f"Onceliklendirme ve risk takibinde orta seviyede tutarliydi. Yogun anlarda destegi kabul ettiginde verimi belirgin sekilde artti.",
            4: f"Ekip ici iletisimde daha seffaf olmaya basladi ve yardimlasma davranisi guclendi. Sahiplenme seviyesi haftanin ikinci yarisinda daha olumlu gorundu.",
        }
        score_map = {
            1: (3, 3, 3, 4),
            2: (3, 4, 3, 4),
            3: (3, 3, 4, 4),
            4: (4, 4, 3, 4),
        }

    return text_map[week_number], score_map[week_number]


def build_sales_feedback_payload(employee: Employee, week_number: int, signal: str) -> tuple[str, tuple[int, int, int, int]]:
    team = employee.team or "satis ekibi"
    role = get_role_bucket(employee.position or "Mid")

    if signal == "strong":
        text_map = {
            1: f"Bu hafta musteri gorusmelerinde inanilmaz enerjikti. Musteri ihtiyaclarini cok iyi analiz etti ve ekibe harika paslar atti.",
            2: f"CRM displini ve teklif takibinde {role.lower()} seviyesinde beklenen kaliteyi asarak mukemmel bir is cikardi. Hicbir follow-up kacmadi.",
            3: f"Zorlu itirazlari yonetmede ve pipeline'i sicak tutmada cok basariliydi. Hedeflere kosarken muthis bir ivme yakaladi.",
            4: f"Baski altindayken bile hedefe kilitlendi, olumlu tutumuyla etrafindakilere de enerji verdi.",
        }
        score_map = {1: (5, 5, 4, 5), 2: (4, 5, 4, 5), 3: (5, 4, 5, 5), 4: (5, 5, 4, 4)}
    elif signal == "watch":
        text_map = {
            1: f"Bu hafta gorusmelerde biraz dalgin gorundu, musterilerle olan iletisimi her zamanki kadar akici degildi.",
            2: f"Teklif hazirliklarinda ve veri girisinde gecikmeler oldu, surec disiplini konusunda desteke ihtiyaci vardi.",
            3: f"Pipeline daki firsatlari takipte yavas kaldi, kapatma odakli degil daha cok savunmada gorundu.",
            4: f"Hedef baskisi motivasyonunu olumsuz etkiledi, geri bildirimleri karsilamada biraz kapaliydi.",
        }
        score_map = {1: (2, 2, 2, 2), 2: (2, 2, 2, 3), 3: (2, 2, 2, 2), 4: (2, 2, 2, 2)}
    else:
        text_map = {
            1: f"Musteri iletisimi iyiydi, ancak bazi spesifik urun sorularinda ekibe danismasi gerekti. Isbirligine acikti.",
            2: f"CRM takibi genel olarak yeterli, bazi notlari daha detayli yazmasi sureci daha da hizlandirabilir.",
            3: f"Satis hedeflerini tutturma yonunde kararli bir cizgisi vardi, istikrarli bir efor gosterdi.",
            4: f"Hafta sonuna dogru toparlandi ve ekiple uyum icinde gorusmeleri yonetti.",
        }
        score_map = {1: (3, 4, 3, 4), 2: (3, 3, 3, 4), 3: (4, 3, 4, 3), 4: (4, 4, 3, 4)}

    return text_map[week_number], score_map[week_number]

def get_peer_sender(employee: Employee, team_members: list[Employee], week_number: int) -> Employee:
    ordered = sorted(team_members, key=lambda item: item.external_employee_code or "")
    index = next(i for i, member in enumerate(ordered) if member.id == employee.id)
    offset = -1 if week_number in {1, 4} else 1
    return ordered[(index + offset) % len(ordered)]


def create_weekly_feedback_history(employees: list[Employee], questions: list[FeedbackQuestion]) -> list[FeedbackResponse]:
    print("Haftalik 360 feedback kayitlari olusturuluyor...")
    employees_no_mgmt = [employee for employee in employees if employee.team != "Yonetim"]
    managers = {employee.department_id: employee for employee in employees if employee.team == "Yonetim"}
    
    team_map: dict[str, list[Employee]] = {}
    for employee in employees_no_mgmt:
        team_map.setdefault(employee.team or "Genel", []).append(employee)

    question_map = get_feedback_question_map(questions)
    anchor_dates = get_feedback_anchor_dates()
    created_rows: list[FeedbackResponse] = []

    for week_number in range(1, 5):
        for employee in employees_no_mgmt:
            if week_number == 3:
                # Eger yonetici bulunamazsa ilk yoneticiyi varsayilan olarak alalim
                sender = managers.get(employee.department_id) or list(managers.values())[0]
                direction = FeedbackDirection.manager_to_employee
            else:
                sender = get_peer_sender(employee, team_map[employee.team or "Genel"], week_number)
                direction = FeedbackDirection.peer_to_peer

            question = question_map[(week_number, direction, employee.department_id)]
            
            if employee.department and employee.department.name == SOFTWARE_DEPARTMENT_NAME:
                response_text, scores = build_feedback_payload(employee, week_number, classify_employee_signal(employee))
            else:
                response_text, scores = build_sales_feedback_payload(employee, week_number, classify_employee_signal(employee))

            created_at = datetime.combine(anchor_dates[week_number], datetime.min.time()).replace(
                hour=9 + (employee.id % 6),
                minute=(employee.id * 7) % 50,
            )

            row = FeedbackResponse(
                sender_id=sender.id,
                receiver_id=employee.id,
                question_id=question.id,
                response_text=response_text,
                score_communication=scores[0],
                score_teamwork=scores[1],
                score_leadership=scores[2],
                score_technical=scores[3],
                period_week=week_number,
                period_month=created_at.month,
                period_year=created_at.year,
                nlp_analysis=None,
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(row)
            db.flush()

            analysis_payload = AIService._fallback_weekly_analysis(
                dept_name=employee.department.name if employee.department else SOFTWARE_DEPARTMENT_NAME,
                question_text=question.question_text,
                response_text=row.response_text,
                score_communication=float(row.score_communication),
                score_teamwork=float(row.score_teamwork),
                score_leadership=float(row.score_leadership),
                score_technical=float(row.score_technical),
            )
            provider = "heuristic"
            model_name = "seed-local-fallback-v1"

            analysis = NLPService.save_weekly_analysis(
                db,
                feedback_response=row,
                analysis_payload=analysis_payload,
                analysis_version="seed-v1",
                model_provider=provider,
                model_name=model_name,
            )
            analysis.created_at = created_at
            analysis.updated_at = created_at

            memory = RAGService.upsert_weekly_feedback_memory(
                db,
                feedback_response=row,
                analysis_payload=analysis_payload,
            )
            memory.created_at = created_at
            memory.updated_at = created_at
            created_rows.append(row)

    db.commit()

    current_year = date.today().year
    current_month = date.today().month
    for employee in employees_no_mgmt:
        NLPService.refresh_employee_monthly_badges(
            db,
            employee_id=employee.id,
            period_year=current_year,
            period_month=current_month,
        )

    db.commit()
    print(f"{len(created_rows)} haftalik feedback kaydi olusturuldu.")
    return created_rows


def print_seed_summary(
    *,
    users: list[User],
    departments: list[Department],
    employees: list[Employee],
    kpis: list[KPI],
    kpi_records: list[KPIRecord],
    survey_responses: list[SurveyResponse],
    feedback_questions: list[FeedbackQuestion],
    feedback_responses: list[FeedbackResponse] | None = None,
) -> None:
    feedback_count_line = (
        f"- {len(feedback_responses)} haftalik feedback kaydi"
        if feedback_responses is not None
        else "- Haftalik feedback kaydi yuklenmedi"
    )

    print("\nSeed tamamlandi!")
    print(
        f"- {len(users)} kullanici\n"
        f"- {len(departments)} departman\n"
        f"- {len(employees)} employee\n"
        f"- {len(kpis)} KPI tanimi\n"
        f"- {len(kpi_records)} KPI kaydi\n"
        f"- {len(survey_responses)} anket cevabi\n"
        f"- {len(feedback_questions)} feedback sorusu\n"
        f"{feedback_count_line}"
    )
    print("\nTest hesaplari:")
    print("Admin: admin@propel.com / admin123")
    print("Yazilim Manager: manager.yazilim@propel.com / manager123")
    print("Ornek Calisan: developer1@propel.com / dev123")


def run_core_seed() -> dict[str, object]:
    print("Software core seed baslatiliyor...\n")
    clear_all_data()
    users = create_users()
    departments = create_departments()
    employees = create_employees(users, departments)
    kpis, kpi_map = create_kpis(departments)
    kpi_records = create_kpi_records(employees, kpi_map)
    survey_responses = create_survey_responses(employees)
    feedback_questions = create_feedback_questions(departments)
    payload = {
        "users": users,
        "departments": departments,
        "employees": employees,
        "kpis": kpis,
        "kpi_map": kpi_map,
        "kpi_records": kpi_records,
        "survey_responses": survey_responses,
        "feedback_questions": feedback_questions,
    }
    print_seed_summary(
        users=users,
        departments=departments,
        employees=employees,
        kpis=kpis,
        kpi_records=kpi_records,
        survey_responses=survey_responses,
        feedback_questions=feedback_questions,
    )
    return payload


def run_analytics_seed() -> dict[str, object]:
    payload = run_core_seed()
    feedback_responses = create_weekly_feedback_history(
        payload["employees"],
        payload["feedback_questions"],
    )
    payload["feedback_responses"] = feedback_responses
    print_seed_summary(
        users=payload["users"],
        departments=payload["departments"],
        employees=payload["employees"],
        kpis=payload["kpis"],
        kpi_records=payload["kpi_records"],
        survey_responses=payload["survey_responses"],
        feedback_questions=payload["feedback_questions"],
        feedback_responses=feedback_responses,
    )
    return payload


if __name__ == "__main__":
    run_core_seed()
    db.close()
