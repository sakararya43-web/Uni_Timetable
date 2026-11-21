from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import AcademicYear, Department, Student, Subject
from app.models.audit import AuditLog
from app.models.enums import AuditAction, CycleStatus, EnrollmentStatus, EntityStatus
from app.models.scheduling import SchedulingCycle
from tests.conftest import make_auth_user


def setup_enrollment_test_data(db: Session, admin_headers: dict):
    # Department
    dept = Department(code="AERO", name="Aerospace Engineering", status=EntityStatus.ACTIVE)
    db.add(dept)
    db.flush()

    # Academic Year
    ay = AcademicYear(
        name="2026-2027-ENR",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
        status=EntityStatus.ACTIVE,
    )
    db.add(ay)
    db.flush()

    # Scheduling Cycle
    cycle = SchedulingCycle(
        academic_year_id=ay.id,
        name="Fall 2026 Aero End-Term",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 15),
        timezone="UTC",
        status=CycleStatus.DRAFT,
        data_version=1,
    )
    db.add(cycle)
    db.flush()

    # Active Subject
    sub = Subject(
        subject_code="AERO101",
        subject_name="Aerodynamics I",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        priority=1,
        status=EntityStatus.ACTIVE,
    )
    # Archived Subject
    archived_sub = Subject(
        subject_code="AERO_OLD",
        subject_name="Old Flight Dynamics",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        priority=1,
        status=EntityStatus.ARCHIVED,
    )
    # Active Student
    student = Student(
        student_number="AERO-001",
        full_name="Bob Pilot",
        department_id=dept.id,
        semester=1,
        status=EntityStatus.ACTIVE,
    )
    # Archived Student
    archived_student = Student(
        student_number="AERO-ARCH",
        full_name="Archived Pilot",
        department_id=dept.id,
        semester=1,
        status=EntityStatus.ARCHIVED,
    )
    db.add_all([sub, archived_sub, student, archived_student])
    db.commit()
    db.refresh(cycle)
    db.refresh(sub)
    db.refresh(archived_sub)
    db.refresh(student)
    db.refresh(archived_student)

    return cycle, sub, archived_sub, student, archived_student


def test_enrollment_lifecycle_and_staleness_signaling(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="enr_admin@univ.edu")
    cycle, sub, arch_sub, student, arch_st = setup_enrollment_test_data(db_session, admin_headers)

    initial_version = cycle.data_version

    # 1. Reject enrolling archived student
    resp_arch_st = client.post(
        "/api/v1/enrollments",
        json={"studentId": arch_st.id, "subjectId": sub.id, "cycleId": cycle.id},
        headers=admin_headers,
    )
    assert resp_arch_st.status_code == 422
    assert resp_arch_st.json()["error"]["code"] == "STUDENT_ARCHIVED"

    # 2. Reject enrolling into archived subject
    resp_arch_sub = client.post(
        "/api/v1/enrollments",
        json={"studentId": student.id, "subjectId": arch_sub.id, "cycleId": cycle.id},
        headers=admin_headers,
    )
    assert resp_arch_sub.status_code == 422
    assert resp_arch_sub.json()["error"]["code"] == "SUBJECT_ARCHIVED"

    # 3. Create active enrollment (P3.12)
    resp_enr = client.post(
        "/api/v1/enrollments",
        json={"studentId": student.id, "subjectId": sub.id, "cycleId": cycle.id},
        headers=admin_headers,
    )
    assert resp_enr.status_code == 201
    enr_data = resp_enr.json()
    enr_id = enr_data["id"]
    assert enr_data["status"] == EnrollmentStatus.ACTIVE.value
    assert (enr_data.get("student_number") or enr_data.get("studentNumber")) == "AERO-001"
    assert (enr_data.get("subject_code") or enr_data.get("subjectCode")) == "AERO101"

    # 4. Verify Staleness Signaling: data_version counter incremented (Task P3.16)
    db_session.refresh(cycle)
    assert cycle.data_version == initial_version + 1

    # 5. Derived enrollment count: Subject GET reflects 1 enrollment (Task P3.5)
    resp_sub = client.get(f"/api/v1/subjects/{sub.id}", headers=admin_headers)
    assert resp_sub.status_code == 200
    sub_resp = resp_sub.json()
    enr_count_val = (
        sub_resp.get("enrollment_count")
        if "enrollment_count" in sub_resp
        else sub_resp.get("enrollmentCount")
    )
    assert enr_count_val == 1

    # 6. Reject duplicate active enrollment (P3.12)
    resp_dup = client.post(
        "/api/v1/enrollments",
        json={"studentId": student.id, "subjectId": sub.id, "cycleId": cycle.id},
        headers=admin_headers,
    )
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_ENROLLMENT"

    # 7. Withdraw enrollment (Task P3.13)
    resp_withdraw = client.delete(f"/api/v1/enrollments/{enr_id}", headers=admin_headers)
    assert resp_withdraw.status_code == 200
    assert resp_withdraw.json()["status"] == EnrollmentStatus.WITHDRAWN.value

    # 8. Staleness incremented again on withdrawal
    db_session.refresh(cycle)
    assert cycle.data_version == initial_version + 2

    # 9. Audit trail recorded for both create and withdraw (Task P3.17)
    audit_create = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == enr_id,
            AuditLog.action == AuditAction.ENROLLMENT_CREATE.value,
        )
    )
    assert audit_create is not None

    audit_withdraw = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == enr_id,
            AuditLog.action == AuditAction.ENROLLMENT_WITHDRAW.value,
        )
    )
    assert audit_withdraw is not None


def test_enrollments_validation_diagnostic_report(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="diag_admin@univ.edu")
    cycle, sub, _, student, _ = setup_enrollment_test_data(db_session, admin_headers)

    # Call /enrollments/validate (Task P3.15)
    resp_val = client.get(f"/api/v1/enrollments/validate?cycleId={cycle.id}", headers=admin_headers)
    assert resp_val.status_code == 200
    report = resp_val.json()

    assert "isValid" in report or "is_valid" in report
    assert "duplicateRecordsCount" in report or "duplicate_records_count" in report
    assert "orphanReferencesCount" in report or "orphan_references_count" in report
    assert (
        "studentsWithZeroEnrollmentsCount" in report
        or "students_with_zero_enrollments_count" in report
    )
    assert (
        "subjectsWithZeroEnrollmentsCount" in report
        or "subjects_with_zero_enrollments_count" in report
    )
    assert "cyclesWithZeroExamsCount" in report or "cycles_with_zero_exams_count" in report
    dup_val = (
        report.get("duplicate_records_count")
        if "duplicate_records_count" in report
        else report.get("duplicateRecordsCount")
    )
    assert dup_val == 0
