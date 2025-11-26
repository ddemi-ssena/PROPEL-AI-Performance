from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base

# Base sınıfı oluştur
Base = declarative_base()

# Eğer Base'i extend etmek isterseniz (opsiyonel)
class BaseModel(Base):
    """
    Tüm modeller için ortak alanları içeren temel model
    """
    __abstract__ = True  # Bu sınıf direkt tablo oluşturmaz
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)