from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "propel API"
    API_V1_STR: str = "/api/v1"
    
    # Veritabanı Ayarları
    POSTGRES_USER: str = "postgres"  # ✅ docker-compose ile uyumlu
    POSTGRES_PASSWORD: str = "123456"  # ✅ docker-compose ile uyumlu
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "propel_db"

    # Güvenlik
    SECRET_KEY: str  # ✅ .env'den okunacak, varsayılan yok
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DEBUG: bool = False

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "forbid"
    }
        

    # ✅ Pydantic V2 ile DATABASE_URL otomatik oluştur
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()