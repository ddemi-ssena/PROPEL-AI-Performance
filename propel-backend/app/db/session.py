from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# PostgreSQL bağlantı motoru
engine = create_engine(settings.DATABASE_URL)

# Veritabanı oturumu oluşturucu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency Injection için (API endpointlerinde kullanılacak)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()