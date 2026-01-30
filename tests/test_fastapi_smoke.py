from fastapi.testclient import TestClient

from asgi import app


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_settings_ok():
    client = TestClient(app)
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "data" in data


def test_search_requires_keyword():
    client = TestClient(app)
    resp = client.post("/api/search", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False


def test_analyze_requires_url():
    client = TestClient(app)
    resp = client.post("/api/analyze", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False


def test_analyze_stream_requires_url():
    client = TestClient(app)
    resp = client.post("/api/analyze/stream", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False


def test_user_portrait_requires_uid():
    client = TestClient(app)
    resp = client.post("/api/user/portrait", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False
