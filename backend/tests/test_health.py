"""
Health API Tests
"""
def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "RecoverAI" in data["app"]


def test_api_info_endpoint(client):
    response = client.get("/api-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["documentation"] == "/docs"


def test_root_serves_frontend(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "RecoverAI" in response.text
