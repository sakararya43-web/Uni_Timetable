"""Automated Endpoint Permission Matrix Introspection Test.

PRD §19, Tasks P14.1.
Verifies role-based access control (RBAC) across all registered API routes:
- Unauthenticated requests receive 401 Unauthorized.
- Student roles receive 403 Forbidden for staff/admin endpoints.
- Role boundaries are strictly enforced.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from tests.conftest import make_auth_user


def test_unauthenticated_requests_rejected(client: TestClient) -> None:
    """Verifies that protected administrative and staff endpoints reject unauthenticated calls."""
    protected_endpoints = [
        ("GET", "/api/v1/users"),
        ("GET", "/api/v1/academic/departments"),
        ("GET", "/api/v1/academic/programs"),
        ("GET", "/api/v1/subjects"),
        ("GET", "/api/v1/students"),
        ("GET", "/api/v1/cycles"),
        ("GET", "/api/v1/audit-logs"),
        ("GET", "/api/v1/me/timetable"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, (
            f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"
        )
        body = res.json()
        assert "error" in body or "detail" in body
        if "error" in body:
            assert "code" in body["error"]


def test_student_role_forbidden_from_admin_endpoints(
    client: TestClient, db_session: Session
) -> None:
    """Verifies that authenticated Student accounts receive 403 Forbidden on administrative endpoints."""
    _, student_headers = make_auth_user(
        db=db_session,
        role=RoleEnum.STUDENT.value,
        email="student_matrix@university.edu",
        full_name="Matrix Student",
    )

    admin_endpoints = [
        ("GET", "/api/v1/users"),
        ("POST", "/api/v1/users"),
        ("POST", "/api/v1/academic/departments"),
        ("POST", "/api/v1/academic/programs"),
        ("POST", "/api/v1/subjects"),
        ("POST", "/api/v1/cycles"),
        ("GET", "/api/v1/audit-logs"),
        ("POST", "/api/v1/students/import"),
        ("POST", "/api/v1/imports/batch-123/confirm"),
    ]

    for method, path in admin_endpoints:
        if method == "GET":
            res = client.get(path, headers=student_headers)
        else:
            res = client.post(path, json={}, headers=student_headers)
        assert res.status_code == 403, (
            f"Expected 403 Forbidden for Student on {method} {path}, got {res.status_code}"
        )


def test_faculty_role_forbidden_from_admin_mutations(
    client: TestClient, db_session: Session
) -> None:
    """Verifies that Faculty members cannot perform administrative mutations."""
    _, faculty_headers = make_auth_user(
        db=db_session,
        role=RoleEnum.FACULTY.value,
        email="faculty_matrix@university.edu",
        full_name="Matrix Faculty",
    )

    admin_mutation_endpoints = [
        ("POST", "/api/v1/users"),
        ("POST", "/api/v1/cycles"),
        ("GET", "/api/v1/audit-logs"),
    ]

    for method, path in admin_mutation_endpoints:
        if method == "GET":
            res = client.get(path, headers=faculty_headers)
        else:
            res = client.post(path, json={}, headers=faculty_headers)
        assert res.status_code == 403, (
            f"Expected 403 Forbidden for Faculty on {method} {path}, got {res.status_code}"
        )
