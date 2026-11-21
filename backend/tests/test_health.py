from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the /health endpoint returns 200 OK and valid status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "service" in data
    assert "environment" in data
    # Ensure X-Request-ID is echoed in response headers
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_ready_endpoint(client: TestClient):
    """Test the /ready endpoint checks database connectivity."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_api_v1_status(client: TestClient):
    """Test the API v1 router prefix responds."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["version"] == "v1"


def test_custom_request_id_propagation(client: TestClient):
    """Test that client-provided X-Request-ID is preserved and echoed."""
    custom_id = "test-request-id-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
