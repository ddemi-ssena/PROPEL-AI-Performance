import re

with open("seed_data.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Sales Constants
sales_constants = """
SOFTWARE_DEPARTMENT_NAME = "Yazilim"
SALES_DEPARTMENT_NAME = "Satis"

SALES_EMPLOYEE_SPECS = [
    {"code": "SL-001", "name": "Ali Yilmaz", "team": "Kurumsal Satis", "position": "Senior Sales Representative", "experience_years": 7.5},
    {"code": "SL-002", "name": "Ayse Demir", "team": "Kurumsal Satis", "position": "Mid Sales Representative", "experience_years": 4.2},
    {"code": "SL-003", "name": "Mehmet Kaya", "team": "Kurumsal Satis", "position": "Lead Sales Representative", "experience_years": 9.1},
    {"code": "SL-004", "name": "Fatma Celik", "team": "Bireysel Satis", "position": "Senior Sales Representative", "experience_years": 5.8},
    {"code": "SL-005", "name": "Mustafa Koc", "team": "Bireysel Satis", "position": "Mid Sales Representative", "experience_years": 3.4},
    {"code": "SL-006", "name": "Zeynep Sahin", "team": "Bireysel Satis", "position": "Junior Sales Representative", "experience_years": 1.2},
    {"code": "SL-007", "name": "Ahmet Ozturk", "team": "Musteri Basarisi", "position": "Senior Customer Success", "experience_years": 6.5},
    {"code": "SL-008", "name": "Elif Aydin", "team": "Musteri Basarisi", "position": "Mid Customer Success", "experience_years": 3.8},
    {"code": "SL-009", "name": "Caner Yildiz", "team": "Bireysel Satis", "position": "Junior Sales Representative", "experience_years": 1.5},
    {"code": "SL-010", "name": "Burcu Arslan", "team": "Kurumsal Satis", "position": "Mid Sales Representative", "experience_years": 3.1},
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
"""
content = content.replace('SOFTWARE_DEPARTMENT_NAME = "Yazilim"', sales_constants)

# 2. Update create_users
users_replace = """    users = [
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
        User(
            email="manager.satis@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Mehmet Satis",
            role=UserRole.department_manager,
            is_active=True,
        ),
    ]"""
content = re.sub(r'    users = \[\s*User\(\s*email="admin@propel\.com"[\s\S]*?\]', users_replace, content)

# Also add sales employees to users
sales_users_loop = """
    for spec in SALES_EMPLOYEE_SPECS:
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
"""
content = content.replace("    db.add_all(users)\n    db.commit()", sales_users_loop + "\n    db.add_all(users)\n    db.commit()")

# 3. Update create_departments
dept_replace = """    departments = [
        Department(
            name=SOFTWARE_DEPARTMENT_NAME,
            description="Backend, Frontend, DevOps ve QA takimlarini kapsayan yazilim organizasyonu",
        ),
        Department(
            name=SALES_DEPARTMENT_NAME,
            description="Kurumsal Satis, Bireysel Satis ve Musteri Basarisi takimlarini kapsayan satis organizasyonu",
        )
    ]"""
content = re.sub(r'    departments = \[\s*Department\(\s*name=SOFTWARE_DEPARTMENT_NAME[\s\S]*?\]', dept_replace, content)

# 4. Update create_employees
emp_replace = """    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)
    sales_department = next(dept for dept in departments if dept.name == SALES_DEPARTMENT_NAME)

    employees = [
        Employee(
            user_id=user_map["manager.yazilim@propel.com"].id,
            department_id=software_department.id,
            external_employee_code="MGR-001",
            team="Yonetim",
            position="Yazilim Departman Muduru",
            experience_years=12.0,
            hire_date=date(2021, 1, 11),
        ),
        Employee(
            user_id=user_map["manager.satis@propel.com"].id,
            department_id=sales_department.id,
            external_employee_code="MGR-002",
            team="Yonetim",
            position="Satis Departman Muduru",
            experience_years=10.0,
            hire_date=date(2021, 5, 10),
        )
    ]"""
content = re.sub(r'    software_department = next[\s\S]*?\]', emp_replace, content)

sales_emp_loop = """
    for index, spec in enumerate(SALES_EMPLOYEE_SPECS, start=1):
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
"""
content = content.replace("    db.add_all(employees)\n    db.commit()", sales_emp_loop + "\n    db.add_all(employees)\n    db.commit()")

# 5. Update create_kpis
kpis_replace = """    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)
    sales_department = next(dept for dept in departments if dept.name == SALES_DEPARTMENT_NAME)

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
    
    kpis.extend([
        KPI(
            name=title,
            description=f"{code} | {description}",
            unit=unit,
            department_id=sales_department.id,
            target_value=target_value,
        )
        for code, title, description, unit, target_value in SALES_KPI_DEFINITIONS
    ])"""
content = re.sub(r'    software_department = next[\s\S]*?for code, title, description, unit, target_value in KPI_DEFINITIONS\n    \]', kpis_replace, content)

kpi_map_replace = """    kpi_map = {
        code: kpi.id
        for (code, _, _, _, _), kpi in zip(KPI_DEFINITIONS + SALES_KPI_DEFINITIONS, kpis)
    }"""
content = re.sub(r'    kpi_map = \{[\s\S]*?\}', kpi_map_replace, content)

# 6. Add generate_sales_kpi_values
sales_kpi_func = """

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
"""
content = content.replace("def create_kpi_records", sales_kpi_func + "\ndef create_kpi_records")

# 7. Update create_kpi_records
kpi_records_replace = """    print("KPI kayitlari olusturuluyor...")
    records: list[KPIRecord] = []
    today = date.today()
    employees_no_mgmt = [employee for employee in employees if employee.team != "Yonetim"]

    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        for employee in employees_no_mgmt:
            if employee.department.name == SOFTWARE_DEPARTMENT_NAME:
                values = generate_kpi_values(employee, month_offset)
            else:
                values = generate_sales_kpi_values(employee, month_offset)
                
            for kpi_name, value in values.items():"""
content = re.sub(r'    print\("KPI kayitlari olusturuluyor\.\.\."\)[\s\S]*?for kpi_name, value in values\.items\(\):', kpi_records_replace, content)

# 8. Update survey_responses
survey_replace = """    print("Anket cevaplari olusturuluyor...")
    responses: list[SurveyResponse] = []
    today = date.today()
    employees_no_mgmt = [employee for employee in employees if employee.team != "Yonetim"]

    for week_offset in range(8):
        period_date = today - timedelta(days=7 * week_offset)
        for employee in employees_no_mgmt:"""
content = re.sub(r'    print\("Anket cevaplari olusturuluyor\.\.\."\)[\s\S]*?for employee in software_employees:', survey_replace, content)
content = content.replace("for employee in software_employees:", "for employee in employees_no_mgmt:")

# 9. Update feedback questions
feedback_q_replace = """    software_department = next(dept for dept in departments if dept.name == SOFTWARE_DEPARTMENT_NAME)
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
        # Sales Questions
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
    ]"""
content = re.sub(r'    software_department = next[\s\S]*?department_id=software_department\.id,\n        \),\n    \]', feedback_q_replace, content)

# 10. Update get_feedback_question_map
question_map_replace = """def get_feedback_question_map(questions: list[FeedbackQuestion]) -> dict[tuple[int, FeedbackDirection, int], FeedbackQuestion]:
    return {
        (question.week_number, question.direction, question.department_id): question
        for question in questions
    }"""
content = re.sub(r'def get_feedback_question_map[\s\S]*?\}', question_map_replace, content)

# 11. Create build_sales_feedback_payload
sales_feedback_payload_func = """

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
"""
content = content.replace("def get_peer_sender", sales_feedback_payload_func + "\ndef get_peer_sender")

# 12. Update create_weekly_feedback_history
history_replace = """    print("Haftalik 360 feedback kayitlari olusturuluyor...")
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
                sender = managers.get(employee.department_id) or managers[list(managers.keys())[0]]
                direction = FeedbackDirection.manager_to_employee
            else:
                sender = get_peer_sender(employee, team_map[employee.team or "Genel"], week_number)
                direction = FeedbackDirection.peer_to_peer

            question = question_map[(week_number, direction, employee.department_id)]
            
            if employee.department.name == SOFTWARE_DEPARTMENT_NAME:
                response_text, scores = build_feedback_payload(employee, week_number, classify_employee_signal(employee))
            else:
                response_text, scores = build_sales_feedback_payload(employee, week_number, classify_employee_signal(employee))
"""
content = re.sub(r'    print\("Haftalik 360 feedback kayitlari olusturuluyor\.\.\."\)[\s\S]*?response_text, scores = build_feedback_payload\([\s\S]*?\)', history_replace, content)

content = content.replace("for employee in software_employees:", "for employee in employees_no_mgmt:")

with open("seed_data.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated seed_data.py")
