# seed_data.py
from datetime import date, timedelta
import random
from app.db.session import SessionLocal
from app.db.models.user import User, UserRole
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.kpi import KPI, KPIRecord, KPIUnit
from app.db.models.survey_response import SurveyResponse
from app.core.security import get_password_hash

db = SessionLocal()

def clear_all_data():
    """Tüm verileri temizle"""
    print("🗑️  Mevcut veriler temizleniyor...")
    # Sıralamaya dikkat: önce ilişkili (child) tablolar, sonra parent tablolar
    db.query(SurveyResponse).delete()
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
        # Software Manager
        User(
            email="manager.yazilim@propel.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Ahmet Yılmaz",
            role=UserRole.department_manager,
            is_active=True
        )
    ]
    
    # Employees (Yazılım Departmanı)
    dev_names = ["Canan Dağdelen", "Berkant Demir", "Elif Öztürk", "Murat Kaya", "Selin Yılmaz"]
    for i in range(1, 6):
        users.append(User(
            email=f"developer{i}@propel.com",
            hashed_password=get_password_hash("dev123"),
            full_name=dev_names[i-1],
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
        Department(name="İnsan Kaynakları", description="İK ve yönetim ekibi"),
    ]
    
    db.add_all(departments)
    db.commit()
    
    print(f"✅ {len(departments)} departman oluşturuldu!")
    return departments

def create_employees(users, departments):
    """Çalışanlar oluştur"""
    print("👥 Çalışanlar oluşturuluyor...")
    
    employees = []
    hire_dates = [date(2023, 1, 15), date(2023, 6, 1), date(2024, 1, 10)]
    
    # Admin (index 0)
    employees.append(Employee(
        user_id=users[0].id,
        department_id=departments[1].id, # İK
        position="Genel Müdür",
        hire_date=hire_dates[0]
    ))
    
    # Yazılım Manager (users[1])
    employees.append(Employee(
        user_id=users[1].id,
        department_id=departments[0].id,
        position="Yazılım Müdürü",
        hire_date=hire_dates[0]
    ))
    
    # Yazılım Developers (5)
    for i in range(2, 7):
        employees.append(Employee(
            user_id=users[i].id,
            department_id=departments[0].id,
            position="Yazılım Geliştirici",
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

def main():
    print("🚀 Seed data başlatılıyor...\n")
    
    clear_all_data()
    users = create_users()
    departments = create_departments()
    employees = create_employees(users, departments)
    kpis, kpi_map, dept_map = create_kpis(departments)
    kpi_records = create_kpi_records(employees, kpi_map, dept_map)
    survey_responses = create_survey_responses(employees)
    
    print("\n✅ Seed data tamamlandı!")
    print(f"""
📊 Özet:
- {len(users)} kullanıcı
- {len(departments)} departman
- {len(employees)} çalışan
- {len(kpis)} KPI tanımı
- {len(kpi_records)} KPI kaydı
- {len(survey_responses)} anket cevabı
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
