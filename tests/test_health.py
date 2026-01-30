from fastapi.testclient import TestClient

from src.backend_fastapi.app import create_app


def test_health() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("success") is True
