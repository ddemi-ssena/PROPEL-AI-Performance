from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_current_user
from app.analytics.artifacts.software import SoftwareArtifactStore
from app.db.base_class import Base
from app.db.models.data_upload import DataUpload
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.services.software_ml_service import SoftwareMLService
from main import app


def _software_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for employee_id, team in ((1, "Backend"), (2, "Frontend"), (3, "QA")):
        for week in range(1, 17):
            risky_period = week >= 11 and employee_id != 2
            rows.append(
                {
                    "employee_id": str(employee_id),
                    "team": team,
                    "role": "Senior" if employee_id == 1 else "Mid",
                    "experience_years": "6" if employee_id == 1 else "3",
                    "week": str(week),
                    "year": "2026",
                    "KPI-1_Gorev_Tamamlama_Orani_GTO": "0.92" if not risky_period else "0.58",
                    "KPI-5_Bug_Yogunlugu_BY": "0.20" if not risky_period else "0.82",
                    "KPI-15_Motivasyon_Skoru_MS": "82" if not risky_period else "50",
                    "performance_band": "Guclu" if employee_id == 2 else ("Stabil" if week < 11 else "Riskli"),
                }
            )
    return rows


@pytest.fixture()
def analytics_client(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "analytics.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr("app.services.software_ml_service.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.services.upload_service.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.services.software_ml_service.SoftwareArtifactStore", lambda: SoftwareArtifactStore(artifact_root))

    db = TestingSessionLocal()
    user = User(
        email="manager@test.local",
        hashed_password="unused",
        full_name="Manager Test",
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    upload = DataUpload(
        file_name="software.csv",
        file_type="Performans Metrikleri (KPI)",
        uploaded_by_id=user.id,
        status="Success",
        record_count=len(_software_rows()),
        raw_info={"department_key": "software"},
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    upload_path = upload_dir / f"{upload.id}_{upload.file_name}"
    headers = list(_software_rows()[0].keys())
    upload_path.write_text(
        ",".join(headers)
        + "\n"
        + "\n".join(",".join(row[column] for column in headers) for row in _software_rows()),
        encoding="utf-8",
    )
    current_user = user
    db.close()

    def override_get_db():
        test_db = TestingSessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    def override_get_current_user():
        return current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as client:
        yield client, upload.id
    app.dependency_overrides.clear()


def test_software_train_state_bulk_prediction_endpoint_flow(analytics_client):
    client, upload_id = analytics_client

    train_response = client.post(
        "/api/v1/analytics/departments/software/models/train",
        json={
            "upload_id": upload_id,
            "target_column": "performance_band",
            "model_name": "random_forest",
            "test_period_count": 4,
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert train_response.status_code == 200
    trained = train_response.json()
    assert trained["upload_id"] == upload_id
    assert trained["target_column"] == "performance_band"
    assert trained["train_count"] > 0
    assert trained["test_count"] > 0

    state_response = client.get(
        f"/api/v1/analytics/departments/software/datasets/{upload_id}/model-state",
        headers={"Authorization": "Bearer test-token"},
    )
    assert state_response.status_code == 200
    performance_state = next(item for item in state_response.json() if item["target_column"] == "performance_band")
    assert performance_state["is_trained"] is True
    assert performance_state["is_current_dataset"] is True

    bulk_response = client.get(
        "/api/v1/analytics/departments/software/predictions/bulk",
        params={"upload_id": upload_id, "target_column": "performance_band"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert bulk_response.status_code == 200
    bulk = bulk_response.json()
    assert bulk["prediction_count"] == 3
    assert len(bulk["items"]) == 3
    assert len(bulk["team_narratives"]) == 3
    assert bulk["department_narrative"]["source"] == "deterministic"


def test_admin_upload_then_software_train_and_predict_flow(analytics_client):
    client, _existing_upload_id = analytics_client
    rows = _software_rows()
    headers = list(rows[0].keys())
    csv_payload = (
        ",".join(headers)
        + "\n"
        + "\n".join(",".join(row[column] for column in headers) for row in rows)
    ).encode("utf-8")

    upload_response = client.post(
        "/api/v1/admin/uploads/",
        data={
            "file_type": "Performans Metrikleri (KPI)",
            "department_key": "software",
        },
        files={"file": ("software-upload.csv", csv_payload, "text/csv")},
    )

    assert upload_response.status_code == 201
    upload = upload_response.json()
    assert upload["status"] == "Success"
    assert upload["record_count"] == len(rows)
    assert upload["raw_info"]["department_key"] == "software"

    train_response = client.post(
        "/api/v1/analytics/departments/software/models/train",
        json={
            "upload_id": upload["id"],
            "target_column": "performance_band",
            "model_name": "random_forest",
            "test_period_count": 4,
        },
    )

    assert train_response.status_code == 200
    bulk_response = client.get(
        "/api/v1/analytics/departments/software/predictions/bulk",
        params={"upload_id": upload["id"], "target_column": "performance_band"},
    )

    assert bulk_response.status_code == 200
    bulk = bulk_response.json()
    assert bulk["prediction_count"] == 3
    assert {item["summary_payload"]["team"] for item in bulk["items"]} == {"Backend", "Frontend", "QA"}
