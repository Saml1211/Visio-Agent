import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_jina_health_endpoint():
    response = client.get("/health/jina")
    assert response.status_code == 200
    assert response.json()["status"] in ["ready", "warming_up"]
    assert "connections" in response.json() 