from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.app_name}
