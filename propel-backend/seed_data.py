# seed_data.py
from datetime import date, timedelta
import random
from app.db.session import SessionLocal
from app.db.models.user import User, UserRole
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.kpi import KPI, KPIRecord, KPIUnit
from app.db.models.survey_response import SurveyResponse
from app.db.models.feedback import FeedbackQuestion, FeedbackDirection, FeedbackResponse
from app.core.security import get_password_hash

db = SessionLocal()

def clear_all_data():
    """Tüm verileri temizle"""
    print("🗑️  Mevcut veriler temizleniyor...")
    # Sıralamaya dikkat: önce ilişkili (child) tablolar, sonra parent tablolar
    db.query(SurveyResponse).delete()
    db.query(FeedbackResponse).delete()
    db.query(FeedbackQuestion).delete()
    db.query(KPIRecord).delete()
    db.query(KPI).delete()
    db.query(Employee).delete()
    db.query(User).delete()
    db.query(Department).delete()
    db.commit()
    print("✅ Veriler temizlendi!")

def create_users():
    """Test kullanıcıları oluştur"""
    print("👤 Kullanıcılar oluşturuluyor...")
    
    users = [
        # Admin
        User(
            email="admin@propel.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin Kullanıcı",
            role=UserRole.admin,
            is_active=True
        ),
        # Department Managers
        User(
            email="manager.yazilim@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Ahmet Yılmaz",
            role=UserRole.department_manager,
            is_active=True
        ),
        User(
            email="manager.satis@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Ayşe Kaya",
            role=UserRole.department_manager,
            is_active=True
        ),
        User(
            email="manager.pazarlama@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Mehmet Demir",
            role=UserRole.department_manager,
            is_active=True
        ),
    ]
    
    # Employees (Yazılım Departmanı)
    dev_names = [
        "Canan Dağdelen", "Berkant Demir", "Elif Öztürk", "Murat Kaya", 
        "Selin Yılmaz", "Caner Yıldız", "Zeynep Çelik", "Burak Şahin",
        "Gamze Arslan", "Onur Polat"
    ]
    for i in range(1, 11):
        users.append(User(
            email=f"developer{i}@propel.com",
            hashed_password=get_password_hash("dev123"),
            full_name=dev_names[i-1],
            role=UserRole.employee,
            is_active=True
        ))
    
    # Employees (Satış Departmanı)
    for i in range(1, 8):
        users.append(User(
            email=f"sales{i}@propel.com",
            hashed_password=get_password_hash("sales123"),
            full_name=f"Satış Temsilcisi {i}",
            role=UserRole.employee,
            is_active=True
        ))
    
    # Employees (Pazarlama Departmanı)
    for i in range(1, 6):
        users.append(User(
            email=f"marketing{i}@propel.com",
            hashed_password=get_password_hash("marketing123"),
            full_name=f"Pazarlama Uzmanı {i}",
            role=UserRole.employee,
            is_active=True
        ))
    
    db.add_all(users)
    db.commit()
    
    print(f"✅ {len(users)} kullanıcı oluşturuldu!")
    return users

def create_departments():
    """Departmanlar oluştur"""
    print("🏢 Departmanlar oluşturuluyor...")
    
    departments = [
        Department(name="Yazılım Geliştirme", description="Backend ve Frontend ekibi"),
        Department(name="Satış", description="B2B ve B2C satış ekibi"),
        Department(name="Pazarlama", description="Dijital pazarlama ve içerik ekibi"),
        Department(name="İnsan Kaynakları", description="İK ve eğitim ekibi"),
    ]
    
    db.add_all(departments)
    db.commit()
    
    print(f"✅ {len(departments)} departman oluşturuldu!")
    return departments

def create_employees(users, departments):
    """Çalışanlar oluştur"""
    print("👥 Çalışanlar oluşturuluyor...")

    employees = []
    hire_dates = [date(2023, 1, 15), date(2023, 6, 1), date(2024, 1, 10), date(2024, 6, 15)]
    dept_map = {d.name: d.id for d in departments}
    user_map = {u.email: u for u in users}

    employees.append(Employee(
        user_id=user_map["manager.yazilim@propel.com"].id,
        department_id=dept_map["Yazılım Geliştirme"],
        position="Yazılım Müdürü",
        hire_date=hire_dates[0]
    ))
    employees.append(Employee(
        user_id=user_map["manager.satis@propel.com"].id,
        department_id=dept_map["Satış"],
        position="Satış Müdürü",
        hire_date=hire_dates[0]
    ))
    employees.append(Employee(
        user_id=user_map["manager.pazarlama@propel.com"].id,
        department_id=dept_map["Pazarlama"],
        position="Pazarlama Müdürü",
        hire_date=hire_dates[0]
    ))

    positions = ["Junior Developer", "Mid-Level Developer", "Senior Developer", "Lead Developer"]
    for i in range(1, 11):
        employees.append(Employee(
            user_id=user_map[f"developer{i}@propel.com"].id,
            department_id=dept_map["Yazılım Geliştirme"],
            position=random.choice(positions),
            hire_date=random.choice(hire_dates)
        ))

    for i in range(1, 8):
        employees.append(Employee(
            user_id=user_map[f"sales{i}@propel.com"].id,
            department_id=dept_map["Satış"],
            position="Satış Temsilcisi",
            hire_date=random.choice(hire_dates)
        ))

    for i in range(1, 6):
        employees.append(Employee(
            user_id=user_map[f"marketing{i}@propel.com"].id,
            department_id=dept_map["Pazarlama"],
            position="Pazarlama Uzmanı",
            hire_date=random.choice(hire_dates)
        ))

    db.add_all(employees)
    db.commit()

    print(f"✅ {len(employees)} çalışan oluşturuldu!")
    return employees

def create_kpis(departments):
    """KPI tanımları oluştur (keyword args ile)"""
    print("📊 KPI'lar oluşturuluyor...")
    
    # departman isim -> id haritası
    dept_map = {d.name: d.id for d in departments}
    
    kpis = [
        # Yazılım KPI'ları
        KPI(
            name="Kod Satırı",
            description="Aylık yazılan kod satırı",
            unit=KPIUnit.numeric,
            department_id=dept_map["Yazılım Geliştirme"],
            target_value=5000
        ),
        KPI(
            name="Bug Sayısı",
            description="Aylık bug sayısı",
            unit=KPIUnit.numeric,
            department_id=dept_map["Yazılım Geliştirme"],
            target_value=5
        ),
        KPI(
            name="Code Review Skoru",
            description="Kod inceleme puanı",
            unit=KPIUnit.percentage,
            department_id=dept_map["Yazılım Geliştirme"],
            target_value=90
        ),
        
        # Satış KPI'ları
        KPI(
            name="Satış Hacmi",
            description="Aylık satış cirosu",
            unit=KPIUnit.currency,
            department_id=dept_map["Satış"],
            target_value=100000
        ),
        KPI(
            name="Yeni Müşteri Sayısı",
            description="Aylık kazanılan müşteri",
            unit=KPIUnit.numeric,
            department_id=dept_map["Satış"],
            target_value=20
        ),
        
        # Pazarlama KPI'ları
        KPI(
            name="Lead Sayısı",
            description="Aylık potansiyel müşteri",
            unit=KPIUnit.numeric,
            department_id=dept_map["Pazarlama"],
            target_value=500
        ),
        KPI(
            name="Conversion Rate",
            description="Lead'den müşteriye dönüşüm oranı",
            unit=KPIUnit.percentage,
            department_id=dept_map["Pazarlama"],
            target_value=15
        ),
        
        # Genel KPI (tüm şirket)
        KPI(
            name="Motivasyon Skoru",
            description="Genel motivasyon puanı",
            unit=KPIUnit.percentage,
            department_id=None,
            target_value=85
        ),
    ]
    
    db.add_all(kpis)
    db.commit()
    
    # commit sonrası gerçek id'leri almak için sorgula
    persisted_kpis = db.query(KPI).all()
    kpi_map = {k.name: k.id for k in persisted_kpis}
    
    print(f"✅ {len(persisted_kpis)} KPI oluşturuldu!")
    return persisted_kpis, kpi_map, dept_map

def create_kpi_records(employees, kpi_map, dept_map):
    """Son 6 ay için KPI kayıtları oluştur (kpi_map kullanılarak)"""
    print("📈 KPI kayıtları oluşturuluyor...")
    
    records = []
    today = date.today()
    
    # Son 6 ay (ay başı gibi yaklaşık)
    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        
        for employee in employees:
            # Yazılım departmanı
            if employee.department_id == dept_map["Yazılım Geliştirme"]:
                # Kod Satırı
                records.append(KPIRecord(
                    kpi_id=kpi_map["Kod Satırı"],
                    employee_id=employee.id,
                    value=random.randint(3000, 7000),
                    period_date=period_date
                ))
                # Bug Sayısı
                records.append(KPIRecord(
                    kpi_id=kpi_map["Bug Sayısı"],
                    employee_id=employee.id,
                    value=random.randint(2, 12),
                    period_date=period_date
                ))
                # Code Review Skoru (opsiyonel, örnek)
                records.append(KPIRecord(
                    kpi_id=kpi_map["Code Review Skoru"],
                    employee_id=employee.id,
                    value=random.randint(70, 100),
                    period_date=period_date
                ))
            
            # Satış departmanı
            elif employee.department_id == dept_map["Satış"]:
                records.append(KPIRecord(
                    kpi_id=kpi_map["Satış Hacmi"],
                    employee_id=employee.id,
                    value=random.randint(50000, 150000),
                    period_date=period_date
                ))
                records.append(KPIRecord(
                    kpi_id=kpi_map["Yeni Müşteri Sayısı"],
                    employee_id=employee.id,
                    value=random.randint(10, 30),
                    period_date=period_date
                ))
            
            # Pazarlama departmanı
            elif employee.department_id == dept_map["Pazarlama"]:
                records.append(KPIRecord(
                    kpi_id=kpi_map["Lead Sayısı"],
                    employee_id=employee.id,
                    value=random.randint(300, 700),
                    period_date=period_date
                ))
                records.append(KPIRecord(
                    kpi_id=kpi_map["Conversion Rate"],
                    employee_id=employee.id,
                    value=random.randint(5, 25),
                    period_date=period_date
                ))
            
            # Genel KPI (her çalışana örnek)
            records.append(KPIRecord(
                kpi_id=kpi_map["Motivasyon Skoru"],
                employee_id=employee.id,
                value=random.randint(60, 100),
                period_date=period_date
            ))
    
    db.add_all(records)
    db.commit()
    
    print(f"✅ {len(records)} KPI kaydı oluşturuldu!")
    return records

def create_survey_responses(employees):
    """Son 6 ay için anket cevapları oluştur"""
    print("📋 Anket cevapları oluşturuluyor...")
    
    responses = []
    today = date.today()
    survey_types = ["motivation", "satisfaction", "stress"]
    
    # Son 6 ay
    for month_offset in range(6):
        period_date = today - timedelta(days=30 * month_offset)
        
        for employee in employees:
            for survey_type in survey_types:
                score = round(random.uniform(2.0, 5.0), 1)
                
                responses.append(SurveyResponse(
                    employee_id=employee.id,
                    survey_type=survey_type,
                    score=score,
                    period_date=period_date,
                    comments=None
                ))
    
    db.add_all(responses)
    db.commit()
    
    print(f"✅ {len(responses)} anket cevabı oluşturuldu!")
    return responses


def create_feedback_questions(departments):
    """Haftalık dinamik feedback soruları oluştur"""
    print("💬 Haftalık feedback soruları oluşturuluyor...")

    dept_map = {d.name: d.id for d in departments}
    yazilim_dept_id = dept_map.get("Yazılım Geliştirme")

    questions = [
        # Genel sorular
        FeedbackQuestion(
            week_number=1,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu hafta teknik olarak en cok hangi blokajla karsilasti ve nasil cozmeye calisti?",
            category="Teknik/Blokajlar",
            department_id=None
        ),
        FeedbackQuestion(
            week_number=2,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu hafta motivasyonunu artiran veya dusuren ana etken neydi?",
            category="Motivasyon",
            department_id=None
        ),
        FeedbackQuestion(
            week_number=3,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Takim ici iletisimde bu hafta en guclu oldugu alan neydi?",
            category="Iletisim",
            department_id=None
        ),
        FeedbackQuestion(
            week_number=4,
            direction=FeedbackDirection.peer_to_peer,
            question_text="Bu ay hangi gelisim alaninda en somut ilerlemeyi gosterdi?",
            category="Gelisim",
            department_id=None
        ),
    ]

    if yazilim_dept_id:
        questions.extend([
            FeedbackQuestion(
                week_number=1,
                direction=FeedbackDirection.peer_to_peer,
                question_text="Bu hafta kod review surecinde sundugu oneriler nasildi?",
                category="Teknik/Blokajlar",
                department_id=yazilim_dept_id
            ),
            FeedbackQuestion(
                week_number=4,
                direction=FeedbackDirection.peer_to_peer,
                question_text="Kullandigimiz yeni framework adaptasyonunda ne kadar ilerledi?",
                category="Gelisim",
                department_id=yazilim_dept_id
            ),
            # Yöneticiden çalışana (manager_to_employee) — yazılım odaklı
            FeedbackQuestion(
                week_number=1,
                direction=FeedbackDirection.manager_to_employee,
                question_text="Bu hafta sprint planina gore teslimatlar ve riskler konusunda ne kadar proaktifti?",
                category="Teknik/Blokajlar",
                department_id=yazilim_dept_id
            ),
            FeedbackQuestion(
                week_number=3,
                direction=FeedbackDirection.manager_to_employee,
                question_text="Bu hafta stakeholder ve ekip ici iletisimde hangi davranisi en faydaliydi?",
                category="Iletisim",
                department_id=yazilim_dept_id
            ),
            # Çalışandan yöneticiye (employee_to_manager) — yazılım odaklı
            FeedbackQuestion(
                week_number=2,
                direction=FeedbackDirection.employee_to_manager,
                question_text="Bu hafta yonetici, blokajlari kaldirmada ve onceliklendirmede ne kadar destekleyiciydi?",
                category="Motivasyon",
                department_id=yazilim_dept_id
            ),
            FeedbackQuestion(
                week_number=4,
                direction=FeedbackDirection.employee_to_manager,
                question_text="Bu ay yonetici, teknik gelisimi (mentorluk, code review kulturü, egitim) ne kadar destekledi?",
                category="Gelisim",
                department_id=yazilim_dept_id
            ),
        ])

    db.add_all(questions)
    db.commit()
    print(f"✅ {len(questions)} haftalık soru oluşturuldu!")
    return questions

def main():
    print("🚀 Seed data başlatılıyor...\n")
    
    clear_all_data()
    users = create_users()
    departments = create_departments()
    employees = create_employees(users, departments)
    kpis, kpi_map, dept_map = create_kpis(departments)
    kpi_records = create_kpi_records(employees, kpi_map, dept_map)
    survey_responses = create_survey_responses(employees)
    feedback_questions = create_feedback_questions(departments)
    
    print("\n✅ Seed data tamamlandı!")
    print(f"""
📊 Özet:
- {len(users)} kullanıcı
- {len(departments)} departman
- {len(employees)} çalışan
- {len(kpis)} KPI tanımı
- {len(kpi_records)} KPI kaydı
- {len(survey_responses)} anket cevabı
- {len(feedback_questions)} haftalık feedback sorusu
    """)
    
    print("🔐 Test Kullanıcıları:")
    print("Admin: admin@propel.com / admin123")
    print("Yazılım Manager: manager.yazilim@propel.com / manager123")
    print("Satış Manager: manager.satis@propel.com / manager123")
    print("Pazarlama Manager: manager.pazarlama@propel.com / manager123")
    print("Developer: developer1@propel.com / dev123")

if __name__ == "__main__":
    main()
    db.close()
