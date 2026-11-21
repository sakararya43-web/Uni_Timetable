from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Student
from app.models.audit import AuditLog
from app.models.enums import AuditAction, EntityStatus
from tests.conftest import make_auth_user


def test_student_crud_and_immutability(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="st_admin@univ.edu")

    # Create department
    resp_dept = client.post(
        "/api/v1/academic/departments",
        json={"code": "CIVIL", "name": "Civil Engineering"},
        headers=admin_headers,
    )
    dept_id = resp_dept.json()["id"]

    # 1. Create valid student
    resp_st = client.post(
        "/api/v1/students",
        json={
            "studentNumber": "STU-2026-001",
            "fullName": "Alice Johnson",
            "email": "alice@univ.edu",
            "departmentId": dept_id,
            "semester": 1,
        },
        headers=admin_headers,
    )
    assert resp_st.status_code == 201
    st_data = resp_st.json()
    st_id = st_data["id"]
    assert (st_data.get("student_number") or st_data.get("studentNumber")) == "STU-2026-001"
    assert (st_data.get("full_name") or st_data.get("fullName")) == "Alice Johnson"
    assert st_data["status"] == EntityStatus.ACTIVE.value

    # 2. Reject duplicate student number
    resp_dup = client.post(
        "/api/v1/students",
        json={
            "studentNumber": "stu-2026-001",
            "fullName": "Duplicate Alice",
            "departmentId": dept_id,
            "semester": 1,
        },
        headers=admin_headers,
    )
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_STUDENT_NUMBER"

    # 3. Update student: student_number is immutable and cannot be altered
    resp_update = client.patch(
        f"/api/v1/students/{st_id}",
        json={"fullName": "Alice Smith"},
        headers=admin_headers,
    )
    assert resp_update.status_code == 200
    up_data = resp_update.json()
    assert (up_data.get("full_name") or up_data.get("fullName")) == "Alice Smith"
    assert (up_data.get("student_number") or up_data.get("studentNumber")) == "STU-2026-001"

    # 4. Search and pagination
    resp_search = client.get("/api/v1/students?search=Alice", headers=admin_headers)
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] >= 1
    assert any(s["id"] == st_id for s in resp_search.json()["items"])

    # 5. Archive student
    resp_arch = client.delete(f"/api/v1/students/{st_id}", headers=admin_headers)
    assert resp_arch.status_code == 200
    assert resp_arch.json()["status"] == EntityStatus.ARCHIVED.value

    # 6. Audit entry written
    audit_entry = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == st_id,
            AuditLog.action == AuditAction.STUDENT_ARCHIVE.value,
        )
    )
    assert audit_entry is not None


def test_student_self_access_scoping(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="st_scope_admin@univ.edu")

    resp_dept = client.post(
        "/api/v1/academic/departments",
        json={"code": "CHEM", "name": "Chemical Engineering"},
        headers=admin_headers,
    )
    dept_id = resp_dept.json()["id"]

    # Create two student users
    u_student1, s1_headers = make_auth_user(
        db_session, role="student", email="s1@univ.edu", full_name="Student One"
    )
    u_student2, s2_headers = make_auth_user(
        db_session, role="student", email="s2@univ.edu", full_name="Student Two"
    )

    # Create student records linked to user IDs
    st1 = Student(
        student_number="S1-001",
        full_name="Student One",
        email="s1@univ.edu",
        department_id=dept_id,
        semester=1,
        user_id=u_student1.id,
        status=EntityStatus.ACTIVE,
    )
    st2 = Student(
        student_number="S2-002",
        full_name="Student Two",
        email="s2@univ.edu",
        department_id=dept_id,
        semester=1,
        user_id=u_student2.id,
        status=EntityStatus.ACTIVE,
    )
    db_session.add_all([st1, st2])
    db_session.commit()
    db_session.refresh(st1)
    db_session.refresh(st2)

    # Student 1 accessing Student 1's record -> OK
    resp_ok = client.get(f"/api/v1/students/{st1.id}", headers=s1_headers)
    assert resp_ok.status_code == 200
    assert (resp_ok.json().get("student_number") or resp_ok.json().get("studentNumber")) == "S1-001"

    # Student 1 accessing Student 2's record -> FORBIDDEN (STUDENT_ACCESS_DENIED)
    resp_denied = client.get(f"/api/v1/students/{st2.id}", headers=s1_headers)
    assert resp_denied.status_code == 403
    assert resp_denied.json()["error"]["code"] == "STUDENT_ACCESS_DENIED"
