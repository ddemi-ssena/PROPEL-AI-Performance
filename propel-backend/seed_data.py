import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base_class import Base
from app.db.models import User, Department, Employee, KPI, KPIRecord, SurveyResponse

# Türkçe veri üretimi için
fake = Faker('tr_TR')

def init_db():
    # Tabloları sıfırdan oluştur (Temiz başlangıç)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def create_departments(db: Session):
    depts = [
        {"name": "Yazılım Geliştirme", "desc": "Ürün geliştirme ve AR-GE"},
        {"name": "Satış ve Pazarlama", "desc": "Müşteri ilişkileri ve satış"},
        {"name": "İnsan Kaynakları", "desc": "Personel yönetimi ve işe alım"},
        {"name": "Müşteri Destek", "desc": "Müşteri sorunları ve ticketlar"}
    ]
    created_depts = []
    for d in depts:
        dept = Department(name=d["name"], description=d["desc"])
        db.add(dept)
        created_depts.append(dept)
    db.commit()
    print(f"✅ {len(created_depts)} Departman oluşturuldu.")
    return created_depts # Nesneleri geri döndür (ID'leri henüz yoksa refresh gerekebilir ama db.query ile çekeceğiz)

def create_kpis(db: Session):
    # Departman ID'lerini çek
    soft_dept = db.query(Department).filter_by(name="Yazılım Geliştirme").first()
    sales_dept = db.query(Department).filter_by(name="Satış ve Pazarlama").first()

    kpis = [
        # Yazılım KPI'ları
        {"name": "Tamamlanan Story Point", "unit": "numeric", "dept_id": soft_dept.id, "target": 40},
        {"name": "Kod Hata Oranı (Bugs)", "unit": "percentage", "dept_id": soft_dept.id, "target": 5},
        # Satış KPI'ları
        {"name": "Aylık Satış Cirosu", "unit": "currency", "dept_id": sales_dept.id, "target": 150000},
        {"name": "Yeni Müşteri Sayısı", "unit": "numeric", "dept_id": sales_dept.id, "target": 10},
        # Genel KPI
        {"name": "Aylık Çalışma Saati", "unit": "numeric", "dept_id": None, "target": 160},
    ]

    for k in kpis:
        db.add(KPI(
            name=k["name"], 
            unit=k["unit"], 
            department_id=k["dept_id"], 
            target_value=k["target"]
        ))
    db.commit()
    print("✅ KPI Tanımları oluşturuldu.")

def create_employees_and_data(db: Session):
    departments = db.query(Department).all()
    kpis = db.query(KPI).all()
    
    # 50 Çalışan Üret
    for _ in range(50):
        # 1. Kullanıcı ve Çalışan Profili Oluştur
        dept = random.choice(departments)
        profile = fake.profile()
        email = profile['mail']
        
        user = User(
            email=email,
            hashed_password="hashed_password_example", # Gerçekte hashlenmeli
            full_name=fake.name(),
            role="employee"
        )
        db.add(user)
        db.commit() # User ID oluşsun

        emp = Employee(
            user_id=user.id,
            department_id=dept.id,
            position=fake.job(),
            hire_date=fake.date_between(start_date='-5y', end_date='-1y')
        )
        db.add(emp)
        db.commit()

        # 2. Bu çalışan için son 12 ayın verisini üret
        start_date = datetime.now() - timedelta(days=365)
        
        # Her ay için döngü
        for i in range(12):
            current_month = start_date + timedelta(days=i*30)
            
            # A. KPI Verileri (Biraz rastgelelik + Mantık)
            # Eğer çalışan "Yazılım"daysa ve KPI "Hata Oranı" ise;
            # Stres yüksekse hata oranını artıracağız (Korelasyon simülasyonu)
            stress_factor = random.randint(1, 5) # 1: Düşük Stres, 5: Yüksek Stres
            
            # Anket Cevabı (Ayda 1 kere)
            survey = SurveyResponse(
                survey_date=current_month,
                employee_id=emp.id,
                stress_score=stress_factor,
                motivation_score=6 - stress_factor, # Ters orantı: Stres yüksekse motivasyon düşük
                satisfaction_score=random.randint(1, 5),
                feedback_text=fake.sentence()
            )
            db.add(survey)

            # KPI Kayıtları
            relevant_kpis = [k for k in kpis if k.department_id == dept.id or k.department_id is None]
            
            for kpi in relevant_kpis:
                base_val = kpi.target_value
                
                # Simülasyon Mantığı:
                # Stres yüksekse (5), performans %20 düşsün
                performance_impact = 1.0
                if stress_factor >= 4:
                    performance_impact = 0.8
                
                # Rastgele dalgalanma (+-%15)
                noise = random.uniform(0.85, 1.15)
                
                final_value = base_val * performance_impact * noise
                
                # Hata oranı gibi "küçük daha iyi" olanlar için mantığı ters çevirmek gerekebilir
                # Ama şimdilik basit tutalım.

                rec = KPIRecord(
                    value=round(final_value, 2),
                    period_date=current_month,
                    employee_id=emp.id,
                    kpi_id=kpi.id
                )
                db.add(rec)
    
    db.commit()
    print("✅ 50 Çalışan ve 1 yıllık geçmiş verileri (Anket + KPI) oluşturuldu.")

def main():
    print("🌱 Veri üretimi başlıyor...")
    db = SessionLocal()
    try:
        init_db()
        create_departments(db)
        create_kpis(db)
        create_employees_and_data(db)
        print("🚀 Veri tabanı başarıyla tohumlandı (Seeded)!")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()