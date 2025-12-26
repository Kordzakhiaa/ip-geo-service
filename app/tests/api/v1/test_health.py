from fastapi import status
from fastapi.testclient import TestClient

from app.core.settings import API_V1_PREFIX
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get(f"{API_V1_PREFIX}/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
