import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Ana endpoint testi"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    """Health endpoint testi"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_invalid_credentials():
    """Geçersiz giriş testi"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "invalid@test.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
