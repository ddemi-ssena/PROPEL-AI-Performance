import pytest
from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.session import engine
from main import app


@pytest.fixture(scope='module')
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def test_read_root(client: TestClient):
    response = client.get('/')
    assert response.status_code == 200
    assert 'message' in response.json()


def test_health_check(client: TestClient):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        '/api/v1/auth/login',
        data={'username': 'invalid@test.com', 'password': 'wrongpass'},
    )
    assert response.status_code == 401
