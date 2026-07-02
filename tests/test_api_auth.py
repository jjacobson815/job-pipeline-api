import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings


@pytest.fixture
def auth_client(mock_settings: Settings) -> TestClient:
    # Use the mock settings
    app = create_app()
    return TestClient(app)


def test_health_endpoint_public(auth_client: TestClient):
    """The /health endpoint should be publicly accessible without authentication."""
    resp = auth_client.get("/health")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"status": "healthy", "version": "0.1.0"}


def test_api_endpoints_reject_without_key(auth_client: TestClient):
    """Router-level security should reject requests with no X-API-Key header."""
    endpoints = [
        ("/api/v1/workers/status", "GET"),
        ("/api/v1/profile/resume", "GET"),
        ("/api/v1/profile/jobs", "GET"),
        ("/api/v1/ingest", "POST"),
        ("/api/v1/analyse", "POST"),
        ("/api/v1/sync", "POST"),
        ("/api/v1/pipeline", "POST"),
        ("/api/v1/jobs/discover", "POST"),
    ]
    
    for url, method in endpoints:
        if method == "GET":
            resp = auth_client.get(url)
        else:
            resp = auth_client.post(url, json={})
        
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json() == {"detail": "Invalid or missing API Key"}


def test_api_endpoints_accept_valid_key(auth_client: TestClient, mock_settings: Settings):
    """Endpoints should accept requests that provide the correct X-API-Key header."""
    headers = {"X-API-Key": mock_settings.api_key}
    
    # Check workers status
    resp = auth_client.get("/api/v1/workers/status", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    
    # Check profile templates
    resp = auth_client.get("/api/v1/profile/resume", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert "resume_text" in resp.json()

    resp = auth_client.get("/api/v1/profile/jobs", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert "jobs_text" in resp.json()


def test_api_endpoints_reject_invalid_key(auth_client: TestClient):
    """Endpoints should reject requests that provide an incorrect API Key."""
    headers = {"X-API-Key": "wrong-secret-key"}
    
    resp = auth_client.get("/api/v1/workers/status", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_batch_url_limit_validation(auth_client: TestClient, mock_settings: Settings):
    """FastAPI/Pydantic validation should reject batches of URLs larger than 10."""
    headers = {"X-API-Key": mock_settings.api_key}
    
    too_many_urls = [f"https://example.com/job-{i}" for i in range(12)]
    
    # Test IngestRequest
    resp = auth_client.post(
        "/api/v1/ingest",
        headers=headers,
        json={"urls": too_many_urls, "source": "custom"}
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "List should have at most 10 items" in resp.text
