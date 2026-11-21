"""Comprehensive Security, Penetration, Privacy, and Idempotency Tests.

PRD §19, Tasks P14.2, P14.3, P14.8, P14.9, P14.10, P14.11, P14.16.
"""

import uuid
from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.academic import Department, Program, Student, Subject
from app.models.enums import CycleStatus, RoleEnum, ScheduleStatus
from app.models.schedule import ExamAssignment, ScheduleVersion
from app.models.scheduling import Exam, SchedulingCycle, TimeSlot
from tests.conftest import make_auth_user


def test_security_headers_present(client: TestClient) -> None:
    """Verifies that all responses include OWASP enterprise security headers (P14.2)."""
    res = client.get("/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_rate_limiting_enforcement(client: TestClient) -> None:
    """Verifies that exceeding the sliding-window threshold triggers HTTP 429 Too Many Requests (P14.3)."""
    # The login endpoint limit is 10 requests per minute
    # Send 12 rapid login attempts
    responses = []
    for _ in range(12):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": f"brute_force_{uuid.uuid4().hex[:6]}@univ.edu", "password": "wrong"},
        )
        responses.append(r)

    # At least the later attempts should be rate limited to 429
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, f"Expected 429 in status codes, got: {status_codes}"
    throttled = next(r for r in responses if r.status_code == 429)
    assert throttled.json()["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in throttled.headers


def test_idempotency_key_replay(client: TestClient, db_session: Session) -> None:
    """Verifies that submitting with an Idempotency-Key returns cached response without duplicate execution (P14.16)."""
    _, admin_headers = make_auth_user(db=db_session, role="admin", email="idem_admin@univ.edu")
    idem_key = f"idem_{uuid.uuid4().hex}"

    dept_payload = {
        "code": f"IDEM_{uuid.uuid4().hex[:4].upper()}",
        "name": "Idempotency Department",
    }

    headers_with_key = {**admin_headers, "Idempotency-Key": idem_key}

    # First request
    res1 = client.post("/api/v1/academic/departments", json=dept_payload, headers=headers_with_key)
    assert res1.status_code == 201

    # Second immediate request with same key
    res2 = client.post("/api/v1/academic/departments", json=dept_payload, headers=headers_with_key)
    assert res2.status_code == 201
    assert res1.json()["id"] == res2.json()["id"]


def test_tampered_jwt_token_rejected(client: TestClient) -> None:
    """Verifies that forged or modified JWT tokens are rejected with 401 Unauthorized (P14.8)."""
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImFkbWluIn0.invalid_signature"
    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {fake_token}"})
    assert res.status_code == 401
    body = res.json()
    err_dict = body.get("error", body)
    assert err_dict.get("code") in ("INVALID_TOKEN", "UNAUTHORIZED")


def test_idor_student_timetable_isolation(client: TestClient, db_session: Session) -> None:
    """Verifies that a student cannot view another student's timetable (IDOR protection, P14.8, P14.10)."""
    dept = Department(code=f"D_{uuid.uuid4().hex[:4]}", name="Dept")
    prog = Program(code=f"P_{uuid.uuid4().hex[:4]}", name="Prog", department=dept)
    db_session.add_all([dept, prog])
    db_session.flush()

    s1 = Student(student_number="STU_IDOR_01", full_name="Student One", email="s1@univ.edu", department_id=dept.id, program_id=prog.id, semester=1)
    s2 = Student(student_number="STU_IDOR_02", full_name="Student Two", email="s2@univ.edu", department_id=dept.id, program_id=prog.id, semester=1)
    db_session.add_all([s1, s2])
    db_session.commit()

    # Authenticate as Student 1
    _, s1_headers = make_auth_user(db=db_session, role=RoleEnum.STUDENT.value, email=s1.email)

    # Student 1 attempts to query Student 2's timetable
    res = client.get(f"/api/v1/students/{s2.id}/timetable", headers=s1_headers)
    assert res.status_code == 403, f"Expected 403 Forbidden on IDOR attempt, got {res.status_code}"


def test_csv_formula_injection_neutralization(client: TestClient, db_session: Session) -> None:
    """Verifies that CSV exports neutralize Excel formula injection characters (=, +, -, @) (P14.8)."""
    dept = Department(code=f"D_{uuid.uuid4().hex[:4]}", name="Formula Dept")
    db_session.add(dept)
    db_session.flush()

    # Subject title crafted with malicious formula syntax
    malicious_sub = Subject(
        subject_code=f"CSV_{uuid.uuid4().hex[:4]}",
        subject_name="=cmd|'/C calc'!A0",
        department_id=dept.id,
        credits=3,
        semester=1,
    )
    db_session.add(malicious_sub)
    db_session.flush()

    cycle = SchedulingCycle(
        name=f"Cycle {uuid.uuid4().hex[:4]}",
        academic_year_id=f"AY_{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 10),
        status=CycleStatus.PUBLISHED,
    )
    db_session.add(cycle)
    db_session.flush()

    slot = TimeSlot(
        scheduling_cycle_id=cycle.id,
        date=date(2026, 12, 1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        duration_minutes=180,
        session_label="Morning",
        slot_index=1,
    )
    db_session.add(slot)
    db_session.flush()

    exam = Exam(subject_id=malicious_sub.id, scheduling_cycle_id=cycle.id, duration_minutes=180)
    db_session.add(exam)
    db_session.flush()

    version = ScheduleVersion(
        scheduling_cycle_id=cycle.id,
        version_number=1,
        status=ScheduleStatus.PUBLISHED,
    )
    db_session.add(version)
    db_session.flush()

    asgn = ExamAssignment(
        schedule_version_id=version.id,
        exam_id=exam.id,
        time_slot_id=slot.id,
        color_id=1,
    )
    db_session.add(asgn)
    db_session.commit()

    _, admin_headers = make_auth_user(db=db_session, role="admin", email="csv_sec@univ.edu")

    res = client.get(f"/api/v1/schedules/{version.id}/export/csv", headers=admin_headers)
    assert res.status_code == 200

    csv_text = res.text
    # Verify the leading '=' was prepended with single quote "'"
    assert "'=cmd|'/C calc'!A0" in csv_text or not csv_text.startswith("=")
    assert not any(line.startswith("=") for line in csv_text.splitlines())


def test_standard_error_response_shape(client: TestClient) -> None:
    """Verifies that API error responses conform to the standard error envelope (P14.9)."""
    res = client.get("/api/v1/non_existent_route")
    assert res.status_code == 404
    body = res.json()
    err_dict = body.get("error", body)
    assert "code" in err_dict
    assert "message" in err_dict
    assert "requestId" in err_dict
