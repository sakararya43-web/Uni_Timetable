from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, UserStatus
from app.models.user import User
from app.utils.security import hash_password


def create_user_fixture(
    db: Session,
    email: str = "testuser@university.edu",
    password: str = "Password123!",
    role: RoleEnum = RoleEnum.FACULTY,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Test User",
        role=role,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_valid_login(client: TestClient, db_session: Session):
    """Test valid login returns tokens and sets cookies (Task P2.8)."""
    email = "validuser@university.edu"
    pwd = "SecretPassword123!"
    create_user_fixture(db_session, email=email, password=pwd, role=RoleEnum.COORDINATOR)

    response = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "coordinator"

    # Verify cookies
    assert "access_token" in response.cookies
    assert "csrf_token" in response.cookies


def test_wrong_password(client: TestClient, db_session: Session):
    """Test login with incorrect password returns 401 INVALID_CREDENTIALS."""
    email = "wrongpwd@university.edu"
    create_user_fixture(db_session, email=email, password="CorrectPassword123!")

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert "Invalid email or password" in data["error"]["message"]


def test_inactive_account(client: TestClient, db_session: Session):
    """Test inactive account login returns 403 ACCOUNT_INACTIVE."""
    email = "inactive@university.edu"
    pwd = "Password123!"
    create_user_fixture(db_session, email=email, password=pwd, status=UserStatus.INACTIVE)

    response = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "ACCOUNT_INACTIVE"


def test_brute_force_lockout(client: TestClient, db_session: Session):
    """Test account is locked out after 5 consecutive failed login attempts (Task P2.11)."""
    email = "lockout@university.edu"
    pwd = "CorrectPassword123!"
    create_user_fixture(db_session, email=email, password=pwd)

    # 5 failed login attempts
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "BadPassword"})
        assert resp.status_code == 401

    # 6th attempt should return 429 ACCOUNT_LOCKED
    lock_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert lock_resp.status_code == 429
    data = lock_resp.json()
    assert data["error"]["code"] == "ACCOUNT_LOCKED"


def test_logout_and_token_invalidation(client: TestClient, db_session: Session):
    """Test logout adds token to denylist and subsequent requests are rejected (Task P2.9)."""
    email = "logout_user@university.edu"
    pwd = "Password123!"
    create_user_fixture(db_session, email=email, password=pwd)

    # Login
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify access to /auth/me
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Attempt to reuse logged out token -> must fail with 401 UNAUTHORIZED
    reused_resp = client.get("/api/v1/auth/me", headers=headers)
    assert reused_resp.status_code == 401
    assert reused_resp.json()["error"]["code"] == "UNAUTHORIZED"
