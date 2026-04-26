from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin_uploads, auth, departments, employees, feedback, feedbacks, kpis, survey_responses
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine
from app.db.vector_support import ensure_pgvector_support, ensure_weekly_pulse_columns


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting API... Creating tables...")
    Base.metadata.create_all(bind=engine)
    ensure_weekly_pulse_columns(engine)
    ensure_pgvector_support(engine)
    yield
    print("Shutting down API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="propel Yapay Zeka Destekli Performans Analiz Sistemi API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(departments.router, prefix=settings.API_V1_STR + "/departments", tags=["Departments"])
app.include_router(employees.router, prefix=settings.API_V1_STR + "/employees", tags=["Employees"])
app.include_router(kpis.router, prefix=settings.API_V1_STR + "/kpis", tags=["KPIs"])
app.include_router(survey_responses.router, prefix=settings.API_V1_STR + "/surveys", tags=["Survey Responses"])
app.include_router(feedback.router, prefix=settings.API_V1_STR + "/feedback", tags=["360 Feedback"])
app.include_router(feedbacks.router, prefix=settings.API_V1_STR + "/feedbacks", tags=["Dynamic Weekly Pulse"])
app.include_router(admin_uploads.router, prefix=settings.API_V1_STR + "/admin/uploads", tags=["Admin Uploads"])


@app.get("/")
def read_root():
    return {"message": "propel API Calisiyor!", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
