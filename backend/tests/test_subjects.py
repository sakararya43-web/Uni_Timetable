from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction, EntityStatus
from tests.conftest import make_auth_user


def test_subject_validation_and_crud(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="sub_admin@univ.edu")

    # Create department
    resp_dept = client.post(
        "/api/v1/academic/departments",
        json={"code": "MATH", "name": "Department of Mathematics"},
        headers=admin_headers,
    )
    dept_id = resp_dept.json()["id"]

    # 1. Reject invalid code format (regex check)
    resp_invalid_code = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "MATH@101#",
            "subjectName": "Calculus I",
            "departmentId": dept_id,
            "semester": 1,
            "credits": 4.0,
            "defaultDurationMinutes": 180,
            "priority": 1,
        },
        headers=admin_headers,
    )
    assert resp_invalid_code.status_code == 422

    # 2. Reject overlapping preferred and restricted dates
    resp_overlap = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "MATH101",
            "subjectName": "Calculus I",
            "departmentId": dept_id,
            "semester": 1,
            "credits": 4.0,
            "defaultDurationMinutes": 180,
            "priority": 1,
            "preferredDates": ["2026-11-05", "2026-11-06"],
            "restrictedDates": ["2026-11-06", "2026-11-07"],
        },
        headers=admin_headers,
    )
    assert resp_overlap.status_code == 422

    # 3. Create valid subject
    resp_sub = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "MATH101",
            "subjectName": "Calculus I",
            "departmentId": dept_id,
            "semester": 1,
            "credits": 4.0,
            "defaultDurationMinutes": 180,
            "priority": 1,
            "preferredDates": ["2026-11-05"],
            "restrictedDates": ["2026-11-07"],
        },
        headers=admin_headers,
    )
    assert resp_sub.status_code == 201
    sub_data = resp_sub.json()
    sub_id = sub_data["id"]
    code_val = sub_data.get("subject_code") or sub_data.get("subjectCode")
    enr_count_val = (
        sub_data.get("enrollment_count")
        if "enrollment_count" in sub_data
        else sub_data.get("enrollmentCount")
    )
    assert code_val == "MATH101"
    assert enr_count_val == 0
    assert sub_data["status"] == EntityStatus.ACTIVE.value

    # 4. Global duplicate code rejection (ADR-009)
    resp_dup = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "math101",
            "subjectName": "Duplicate Calculus",
            "departmentId": dept_id,
            "semester": 1,
        },
        headers=admin_headers,
    )
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_SUBJECT_CODE"

    # 5. Archive subject
    resp_arch = client.delete(f"/api/v1/subjects/{sub_id}", headers=admin_headers)
    assert resp_arch.status_code == 200
    assert resp_arch.json()["status"] == EntityStatus.ARCHIVED.value

    # 6. Verify audit entry exists
    audit_entry = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == sub_id,
            AuditLog.action == AuditAction.SUBJECT_ARCHIVE.value,
        )
    )
    assert audit_entry is not None


def test_subject_coordinator_department_scoping(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="admin_scoping@univ.edu")

    # Create two departments
    d1 = client.post(
        "/api/v1/academic/departments",
        json={"code": "DEPT1", "name": "Department One"},
        headers=admin_headers,
    ).json()["id"]
    d2 = client.post(
        "/api/v1/academic/departments",
        json={"code": "DEPT2", "name": "Department Two"},
        headers=admin_headers,
    ).json()["id"]

    # Create coordinator scoped to DEPT1
    _, coord_headers = make_auth_user(
        db_session,
        role="coordinator",
        email="coord_dept1@univ.edu",
        department_id=d1,
    )

    # Coordinator can create subject in DEPT1
    resp_ok = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "D1-SUB1",
            "subjectName": "Intro to Dept 1",
            "departmentId": d1,
            "semester": 1,
        },
        headers=coord_headers,
    )
    assert resp_ok.status_code == 201

    # Coordinator FORBIDDEN to create subject in DEPT2
    resp_forbidden = client.post(
        "/api/v1/subjects",
        json={
            "subjectCode": "D2-SUB1",
            "subjectName": "Intro to Dept 2",
            "departmentId": d2,
            "semester": 1,
        },
        headers=coord_headers,
    )
    assert resp_forbidden.status_code == 403
    assert resp_forbidden.json()["error"]["code"] == "FORBIDDEN"
