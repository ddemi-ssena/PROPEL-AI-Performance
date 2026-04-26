
from datetime import date, timedelta
import random
from app.db.session import SessionLocal
from app.db.models.survey_response import SurveyResponse
from app.db.models.employee import Employee

db = SessionLocal()

def seed_pulse():
    employees = db.query(Employee).all()
    today = date.today()
    
    print(f"Seeding pulse data for {len(employees)} employees...")
    
    for emp in employees:
        # Son 4 hafta için veri üret
        for i in range(4):
            period_date = today - timedelta(days=7 * i)
            
            # Var mı kontrol et
            existing = db.query(SurveyResponse).filter(
                SurveyResponse.employee_id == emp.id,
                SurveyResponse.survey_type == "weekly_pulse",
                SurveyResponse.period_date == period_date
            ).first()
            
            if existing:
                continue
                
            # Rastgele skorlar
            ms_score = round(random.uniform(3.0, 5.0), 2)
            mte_score = round(random.uniform(-0.1, 0.4), 3)
            ars_score = round(random.uniform(0.0, 0.8), 3)
            
            res = SurveyResponse(
                employee_id=emp.id,
                survey_type="weekly_pulse",
                score=ms_score,
                period_date=period_date,
                mte_score=mte_score,
                ars_score=ars_score,
                raw_data={"q1": 4, "q2": 4, "q3": 4, "q4": "Sample", "q5": "Sample", "q6": "Sample"},
                comments="Seeded pulse data"
            )
            db.add(res)
            
    db.commit()
    print("✅ Seeded successfully!")

if __name__ == "__main__":
    seed_pulse()
    db.close()
