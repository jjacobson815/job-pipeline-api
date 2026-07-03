import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_db
from app.domains.auth.models import User
from app.domains.auth.security import hash_password

# Clean in-memory SQLite schema for api auth tests with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed a default test user
        user = User(email="test@example.com", hashed_password=hash_password("pw123"))
        db.add(user)
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_client(test_db) -> TestClient:
    app = create_app()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def jwt_token(auth_client: TestClient) -> str:
    """Authenticates the default user and yields a valid JWT token."""
    resp = auth_client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "pw123"}
    )
    return resp.json()["access_token"]


def test_health_endpoint_public(auth_client: TestClient):
    """The /health endpoint should be publicly accessible without authentication."""
    resp = auth_client.get("/health")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"status": "healthy", "version": "0.1.0"}


def test_api_endpoints_reject_without_token(auth_client: TestClient):
    """Router-level security should reject requests with no authorization header."""
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
        assert "Not authenticated" in resp.text or "credentials" in resp.text


def test_api_endpoints_accept_valid_token(auth_client: TestClient, jwt_token: str):
    """Endpoints should accept requests that provide the correct Bearer token."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
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


def test_api_endpoints_reject_invalid_token(auth_client: TestClient):
    """Endpoints should reject requests that provide an incorrect JWT token."""
    headers = {"Authorization": "Bearer wrong-token-123"}
    
    resp = auth_client.get("/api/v1/workers/status", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_batch_url_limit_validation(auth_client: TestClient, jwt_token: str):
    """FastAPI/Pydantic validation should reject batches of URLs larger than 10."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    too_many_urls = [f"https://example.com/job-{i}" for i in range(12)]
    
    resp = auth_client.post(
        "/api/v1/ingest",
        headers=headers,
        json={"urls": too_many_urls, "source": "custom"}
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "List should have at most 10 items" in resp.text
