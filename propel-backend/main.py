from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine
from app.db.models import Base
from app.api.routers import auth, departments,  employees

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting API... Creating tables...")
    Base.metadata.create_all(bind=engine)

    yield  # <--- Uygulama bu noktadan sonra çalışmaya devam eder

    # Shutdown
    print("Shutting down API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="propel Yapay Zeka Destekli Performans Analiz Sistemi API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vue.js'in çalışacağı adres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTH router
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(departments.router, prefix=settings.API_V1_STR + "/departments", tags=["Departments"])
app.include_router(employees.router, prefix=settings.API_V1_STR + "/employees", tags=["Employees"])

@app.get("/")
def read_root():
    return {"message": "propel API Çalışıyor!", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
