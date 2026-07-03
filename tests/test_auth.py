import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_db
from app.domains.auth.models import User, PipelineRun
from app.domains.auth.security import hash_password

# Use an in-memory SQLite database with StaticPool to keep schema across connections
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """Setup and teardown a clean in-memory database schema for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db) -> TestClient:
    """FastAPI TestClient with overridden database dependency."""
    app = create_app()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_register_user(client: TestClient):
    """Should successfully register a new user."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient, test_db):
    """Should refuse registration with duplicate email."""
    # Seed a user directly
    user = User(email="test@example.com", hashed_password=hash_password("pw"))
    test_db.add(user)
    test_db.commit()

    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in resp.json()["detail"]


def test_login_success(client: TestClient, test_db):
    """Should issue JWT access token on valid credentials."""
    user = User(email="test@example.com", hashed_password=hash_password("securepassword"))
    test_db.add(user)
    test_db.commit()

    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "securepassword"}
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, test_db):
    """Should deny auth token for incorrect password."""
    user = User(email="test@example.com", hashed_password=hash_password("securepassword"))
    test_db.add(user)
    test_db.commit()

    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in resp.json()["detail"]


def test_get_current_user_profile(client: TestClient, test_db):
    """Should retrieve own user details with valid JWT token."""
    user = User(email="me@example.com", hashed_password=hash_password("pw"))
    test_db.add(user)
    test_db.commit()

    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "me@example.com", "password": "pw"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["email"] == "me@example.com"


def test_get_profile_unauthorized(client: TestClient):
    """Should deny profile fetching when no JWT token is supplied."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_profile(client: TestClient, test_db):
    """Should allow logged-in user to save key overrides and resume."""
    user = User(email="me@example.com", hashed_password=hash_password("pw"))
    test_db.add(user)
    test_db.commit()

    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "me@example.com", "password": "pw"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "resume_text": "Updated resume contents",
            "gemini_api_key": "AQ.personal-gemini-key",
            "teal_api_key": "personal-teal-key"
        }
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["resume_text"] == "Updated resume contents"
    assert data["gemini_api_key"] == "AQ.personal-gemini-key"
    assert data["teal_api_key"] == "personal-teal-key"


def test_multi_user_isolation(client: TestClient, test_db):
    """Verify User A's pipeline runs are completely invisible to User B."""
    # 1. Seed two users
    user_a = User(email="a@example.com", hashed_password=hash_password("pw"))
    user_b = User(email="b@example.com", hashed_password=hash_password("pw"))
    test_db.add(user_a)
    test_db.add(user_b)
    test_db.commit()

    # 2. Add run history for User A
    run = PipelineRun(
        user_id=user_a.id,
        run_id="run-a-123",
        timestamp="2026-07-02T12:00:00Z",
        total_jobs=3,
        succeeded_jobs=3,
        avg_score=85.0,
        result_json='{"status": "ok"}'
    )
    test_db.add(run)
    test_db.commit()

    # 3. Log in as User B
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "b@example.com", "password": "pw"}
    )
    token_b = login_resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. Fetch history as User B (should be empty!)
    resp = client.get("/api/v1/pipeline/history", headers=headers_b)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 0
