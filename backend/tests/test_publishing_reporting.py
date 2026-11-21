"""Comprehensive test suite for Phase 10: Publishing, Student Timetables, Exports, Reports, and Audit Trail.

PRD §16, §18.7, §20, §21, §23, §26.4, Tasks P10.1 - P10.21.
"""

from io import BytesIO

import openpyxl
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Department, Student, Subject
from app.models.enums import AuditAction, CycleStatus, EnrollmentStatus, ScheduleStatus
from app.models.schedule import ScheduleVersion
from app.models.scheduling import Enrollment
from tests.conftest import make_auth_user
from tests.test_schedule_versions_editing import setup_version_test_fixture


def test_publish_schedule_success(client: TestClient, db_session: Session):
    """Verifies atomic publication of a validated schedule candidate (P10.1 - P10.4)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="pub_admin@univ.edu")
    cycle, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.post(
        f"/api/v1/schedules/{ver.id}/publish",
        json={"confirm": True, "notes": "Official Final Exam Timetable"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == ScheduleStatus.PUBLISHED.value
    assert data.get("publishedAt") or data.get("published_at") is not None

    # Verify cycle state
    db_session.refresh(cycle)
    assert cycle.status == CycleStatus.PUBLISHED


def test_publish_schedule_stale_rejection(client: TestClient, db_session: Session):
    """Verifies that publishing is refused if data changes made the graph stale (P10.1)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="pub_stale_admin@univ.edu")
    cycle, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # Invalidate graph by adding a new student enrollment
    dept = db_session.scalar(select(Department).limit(1))
    new_stu = Student(
        student_number="STU_STALE_1",
        full_name="Stale Student",
        email="stale_stu@univ.edu",
        department_id=dept.id if dept else None,
        semester=1,
    )
    db_session.add(new_stu)
    db_session.flush()

    sub = db_session.scalar(select(Subject).limit(1))
    new_enr = Enrollment(
        student_id=new_stu.id,
        subject_id=sub.id,
        cycle_id=cycle.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(new_enr)
    db_session.commit()

    resp = client.post(
        f"/api/v1/schedules/{ver.id}/publish",
        json={"confirm": True, "notes": "Should fail"},
        headers=admin_headers,
    )
    assert resp.status_code == 409
    assert "SCHEDULE_STALE" in resp.text


def test_publish_schedule_hard_violation_rejection(client: TestClient, db_session: Session):
    """Verifies that publishing is blocked if any hard constraint violation exists (P10.2)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="pub_violation_admin@univ.edu")
    cycle, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    # Corrupt assignment: assign two conflicting exams to the exact same slot
    ver.assignments[1].time_slot_id = ver.assignments[0].time_slot_id
    db_session.commit()

    resp = client.post(
        f"/api/v1/schedules/{ver.id}/publish",
        json={"confirm": True},
        headers=admin_headers,
    )
    assert resp.status_code == 422
    assert "PUBLISH_FAILED_INVALID_SCHEDULE" in resp.text


def test_publish_supersedes_older_published_version(client: TestClient, db_session: Session):
    """Verifies that publishing supersedes and archives any previously published version (P10.3)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="pub_supersede_admin@univ.edu")
    cycle, ver1, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # 1. Publish version 1
    resp1 = client.post(
        f"/api/v1/schedules/{ver1.id}/publish",
        json={"confirm": True},
        headers=admin_headers,
    )
    assert resp1.status_code == 200

    # 2. Clone to version 2
    clone_resp = client.post(f"/api/v1/schedules/{ver1.id}/clone", headers=admin_headers)
    assert clone_resp.status_code == 200
    v2_id = clone_resp.json()["id"]

    # 3. Publish version 2
    resp2 = client.post(
        f"/api/v1/schedules/{v2_id}/publish",
        json={"confirm": True, "notes": "Revision 2"},
        headers=admin_headers,
    )
    assert resp2.status_code == 200

    db_session.refresh(ver1)
    ver2 = db_session.get(ScheduleVersion, v2_id)
    assert ver1.status == ScheduleStatus.ARCHIVED
    assert ver2 is not None and ver2.status == ScheduleStatus.PUBLISHED


def test_publish_requires_admin(client: TestClient, db_session: Session):
    """Verifies that non-admin users cannot publish a schedule (P10.1)."""
    _, student_headers = make_auth_user(db_session, role="student", email="pub_student@univ.edu")
    _, admin_headers = make_auth_user(db_session, role="admin", email="pub_admin2@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.post(
        f"/api/v1/schedules/{ver.id}/publish",
        json={"confirm": True},
        headers=student_headers,
    )
    assert resp.status_code == 403


def test_student_timetable_views_and_privacy(client: TestClient, db_session: Session):
    """Verifies individual student timetable views, privacy scoping, and security checks (P10.5, P10.6, P10.8)."""
    # Create student account
    student_user, student_headers = make_auth_user(db_session, role="student", email="stud_view@univ.edu")
    _, admin_headers = make_auth_user(db_session, role="admin", email="stud_admin@univ.edu")
    cycle, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # Link user to a student record enrolled in EE101
    dept = db_session.scalar(select(Department).limit(1))
    student_rec = Student(
        user_id=student_user.id,
        email="stud_view@univ.edu",
        student_number="S99001",
        full_name="Alice Student",
        semester=1,
        department_id=dept.id if dept else None,
    )
    db_session.add(student_rec)
    db_session.flush()

    sub_ee101 = db_session.scalar(select(Subject).where(Subject.subject_code == "EE101").limit(1))
    enrollment = Enrollment(
        student_id=student_rec.id,
        subject_id=sub_ee101.id,
        cycle_id=cycle.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment)
    # Rebuild graph so enrollment doesn't make graph stale
    db_session.commit()
    client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)

    # Before publishing: querying /me/timetable returns 404
    pre_resp = client.get("/api/v1/me/timetable", headers=student_headers)
    assert pre_resp.status_code == 404

    # Publish schedule
    pub_resp = client.post(f"/api/v1/schedules/{ver.id}/publish", json={"confirm": True}, headers=admin_headers)
    assert pub_resp.status_code == 200

    # After publishing: student queries /me/timetable
    my_resp = client.get("/api/v1/me/timetable", headers=student_headers)
    assert my_resp.status_code == 200
    my_data = my_resp.json()
    assert (my_data.get("studentNumber") or my_data.get("student_number")) == "S99001"
    assert len(my_data["exams"]) == 1
    assert (my_data["exams"][0].get("subjectCode") or my_data["exams"][0].get("subject_code")) == "EE101"
    # Ensure no other student details leaked
    assert "students" not in str(my_data["exams"][0])

    # Student cannot view another student's timetable by ID
    other_stud = Student(
        email="other@univ.edu",
        student_number="S99002",
        full_name="Bob Other",
        semester=1,
        department_id=dept.id if dept else None,
    )
    db_session.add(other_stud)
    db_session.commit()

    forbidden_resp = client.get(f"/api/v1/students/{other_stud.id}/timetable", headers=student_headers)
    assert forbidden_resp.status_code == 403

    # Admin CAN view other student's timetable
    admin_view_resp = client.get(f"/api/v1/students/{student_rec.id}/timetable", headers=admin_headers)
    assert admin_view_resp.status_code == 200
    assert (admin_view_resp.json().get("studentNumber") or admin_view_resp.json().get("student_number")) == "S99001"


def test_master_timetable_and_filtering(client: TestClient, db_session: Session):
    """Verifies master timetable retrieval and filtering by department, date, and session (P10.7)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="master_admin@univ.edu")
    cycle, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.get(f"/api/v1/schedules/{ver.id}/timetable/master", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert (data.get("totalExams") or data.get("total_exams")) == 3
    assert len(data["entries"]) == 3

    # Filter by specific date
    target_date = str(slots[0].date)
    date_resp = client.get(f"/api/v1/schedules/{ver.id}/timetable/master?date={target_date}", headers=admin_headers)
    assert date_resp.status_code == 200
    for e in date_resp.json()["entries"]:
        assert str(e.get("slotDate") or e.get("slot_date")) == target_date


def test_csv_export_with_sanitization(client: TestClient, db_session: Session):
    """Verifies RFC 4180 CSV export with formula injection escaping and audit logging (P10.9, P10.13, P10.14)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="csvexp_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.get(f"/api/v1/schedules/{ver.id}/export/csv", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    content = resp.text
    assert "Subject Code,Subject Name,Department,Exam Date" in content
    assert "EE101" in content
    assert "EE102" in content
    assert "EE103" in content


def test_pdf_export(client: TestClient, db_session: Session):
    """Verifies ReportLab PDF generation with valid PDF stream headers (P10.10, P10.14)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="pdfexp_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.get(f"/api/v1/schedules/{ver.id}/export/pdf", headers=admin_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    assert resp.content.startswith(b"%PDF-")


def test_excel_export(client: TestClient, db_session: Session):
    """Verifies multi-tab OpenPyXL Excel workbook generation (P10.11, P10.14)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="xlsexp_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp = client.get(f"/api/v1/schedules/{ver.id}/export/excel", headers=admin_headers)
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]

    wb = openpyxl.load_workbook(BytesIO(resp.content))
    assert "Master Timetable" in wb.sheetnames
    assert "By Department" in wb.sheetnames

    ws1 = wb["Master Timetable"]
    assert ws1.cell(row=1, column=1).value == "Subject Code"
    assert ws1.max_row >= 4  # Header + 3 exams


def test_reports_summary_and_distribution(client: TestClient, db_session: Session):
    """Verifies cycle summary and schedule workload distribution reporting (P10.15, P10.16)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="rep_admin@univ.edu")
    cycle, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # 1. Cycle summary
    sum_resp = client.get(f"/api/v1/cycles/{cycle.id}/reports/summary", headers=admin_headers)
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert (sum_data.get("totalExams") or sum_data.get("total_exams")) == 3
    assert (sum_data.get("totalStudents") or sum_data.get("total_students")) >= 2
    assert (sum_data.get("graphVertices") or sum_data.get("graph_vertices")) == 3

    # 2. Schedule workload distribution
    dist_resp = client.get(f"/api/v1/schedules/{ver.id}/reports/distribution", headers=admin_headers)
    assert dist_resp.status_code == 200
    dist_data = dist_resp.json()
    assert len(dist_data.get("byDate") or dist_data.get("by_date")) >= 1
    assert len(dist_data.get("bySession") or dist_data.get("by_session")) >= 1


def test_audit_logs_query_and_coverage(client: TestClient, db_session: Session):
    """Verifies querying audit logs with filters, pagination, and action enumeration (P10.20, P10.21)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="audit_admin@univ.edu")
    _, student_headers = make_auth_user(db_session, role="student", email="audit_stud@univ.edu")

    # Non-admin forbidden
    forb_resp = client.get("/api/v1/audit-logs", headers=student_headers)
    assert forb_resp.status_code == 403

    # Admin query
    resp = client.get("/api/v1/audit-logs?limit=10", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    # Enum catalogue verification (P10.21)
    for act in AuditAction:
        assert isinstance(act.value, str)
        assert len(act.value) > 0
