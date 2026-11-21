import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, UserStatus
from app.models.user import User
from app.utils.security import create_token, hash_password


def get_token_for_role(db: Session, role: RoleEnum, email: str) -> str:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        full_name=f"User {role.value}",
        role=role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    token, _, _ = create_token(subject=user.id, claims={"role": role.value})
    return token


def test_unauthenticated_request_rejected(client: TestClient):
    """Unauthenticated request to protected endpoint returns 401 UNAUTHORIZED."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "role,allowed",
    [
        (RoleEnum.ADMIN, True),
        (RoleEnum.COORDINATOR, False),
        (RoleEnum.FACULTY, False),
        (RoleEnum.STUDENT, False),
    ],
)
def test_rbac_user_management(
    client: TestClient, db_session: Session, role: RoleEnum, allowed: bool
):
    """
    Parametrized test verifying PRD §7 Role Matrix for User Management.
    Only ADMIN may manage users; other roles must receive 403 FORBIDDEN.
    """
    token = get_token_for_role(db_session, role, f"rbac_{role.value}@university.edu")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users", headers=headers)

    if allowed:
        assert response.status_code == 200
        assert "items" in response.json()
    else:
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_create_and_manage_users(client: TestClient, db_session: Session):
    """Admin creates a user, updates user, and resets password (Task P2.19)."""
    admin_token = get_token_for_role(db_session, RoleEnum.ADMIN, "superadmin@university.edu")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create User
    create_payload = {
        "email": "new_coord@university.edu",
        "password": "Password1234!",
        "full_name": "New Coordinator",
        "role": "coordinator",
    }
    create_resp = client.post("/api/v1/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    user_data = create_resp.json()
    new_user_id = user_data["id"]
    assert user_data["email"] == "new_coord@university.edu"
    assert user_data["role"] == "coordinator"

    # 2. Update User
    update_payload = {"full_name": "Updated Coordinator Name", "role": "faculty"}
    update_resp = client.patch(f"/api/v1/users/{new_user_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    res_data = update_resp.json()
    assert (res_data.get("fullName") or res_data.get("full_name")) == "Updated Coordinator Name"
    assert res_data["role"] == "faculty"

    # 3. Reset Password
    reset_payload = {"new_password": "NewSecretPassword999!"}
    reset_resp = client.post(
        f"/api/v1/users/{new_user_id}/reset-password", json=reset_payload, headers=headers
    )
    assert reset_resp.status_code == 200

    # 4. Verify new password allows login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "new_coord@university.edu", "password": "NewSecretPassword999!"},
    )
    assert login_resp.status_code == 200
