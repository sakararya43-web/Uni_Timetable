import io
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import AcademicYear, Department, Student, Subject
from app.models.audit import AuditLog
from app.models.enums import AuditAction, CycleStatus, EntityStatus, ImportStatus
from app.models.scheduling import SchedulingCycle
from tests.conftest import make_auth_user


def setup_import_base_data(db: Session, admin_headers: dict):
    # Create Departments
    d_cse = Department(
        code="CSE", name="Computer Science & Engineering", status=EntityStatus.ACTIVE
    )
    d_it = Department(code="IT", name="Information Technology", status=EntityStatus.ACTIVE)
    db.add_all([d_cse, d_it])
    db.flush()

    # Create Academic Year
    ay = AcademicYear(
        name="2026-2027-CSV",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
        status=EntityStatus.ACTIVE,
    )
    db.add(ay)
    db.flush()

    # Create Scheduling Cycle
    cycle = SchedulingCycle(
        academic_year_id=ay.id,
        name="Fall 2026 CSV Term",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 20),
        timezone="UTC",
        status=CycleStatus.DRAFT,
        data_version=1,
    )
    db.add(cycle)
    db.commit()
    db.refresh(d_cse)
    db.refresh(d_it)
    db.refresh(cycle)

    return d_cse, d_it, cycle


# ==============================================================================
# 1. Students Import Tests
# ==============================================================================
def test_student_import_preview_and_confirm(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="imp_admin@univ.edu")
    d_cse, d_it, _ = setup_import_base_data(db_session, admin_headers)

    csv_content = (
        "student_id,student_name,department,semester,email\n"
        "S001,Student One,CSE,5,s1@univ.edu\n"
        "S002,Student Two,CSE,5,s2@univ.edu\n"
        "S003,Student Three,IT,5,s3@univ.edu\n"
    )

    # 1. Preview mode
    files = {"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp_prev = client.post(
        "/api/v1/students/import?mode=preview", files=files, headers=admin_headers
    )
    assert resp_prev.status_code == 200
    prev_data = resp_prev.json()

    batch_id = prev_data.get("batch_id") or prev_data.get("batchId")
    assert batch_id is not None
    assert (
        prev_data.get("valid_rows") if "valid_rows" in prev_data else prev_data.get("validRows")
    ) == 3
    assert (
        prev_data.get("invalid_rows")
        if "invalid_rows" in prev_data
        else prev_data.get("invalidRows")
    ) == 0
    assert prev_data.get("status") == ImportStatus.PREVIEW.value

    # 2. Confirm mode
    resp_conf = client.post(
        f"/api/v1/imports/{batch_id}/confirm", json={"skipInvalid": False}, headers=admin_headers
    )
    assert resp_conf.status_code == 200
    conf_data = resp_conf.json()
    committed = (
        conf_data.get("committed_rows")
        if "committed_rows" in conf_data
        else conf_data.get("committedRows")
    )
    assert committed == 3
    assert conf_data.get("status") == ImportStatus.COMMITTED.value

    # Verify database insertion
    st1 = db_session.scalar(select(Student).where(Student.student_number == "S001"))
    assert st1 is not None
    assert st1.full_name == "Student One"
    assert st1.semester == 5


def test_student_import_validation_and_error_reporting(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="imp_val@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    # CSV with intentional errors:
    # Row 2: invalid semester 'five'
    # Row 3: duplicate of row 1 (S010)
    # Row 4: unknown department 'UNKNOWN_DEPT'
    # Row 5: empty name
    csv_content = (
        "student_id,student_name,department,semester\n"
        "S010,Valid Alice,CSE,5\n"
        "S011,Bob Johnson,CSE,five\n"
        "S010,Duplicate S010,CSE,5\n"
        "S012,Charlie,UNKNOWN_DEPT,5\n"
        "S013,,CSE,5\n"
    )

    files = {"file": ("students_err.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/students/import?mode=preview", files=files, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    valid_rows = data.get("valid_rows") if "valid_rows" in data else data.get("validRows")
    invalid_rows = data.get("invalid_rows") if "invalid_rows" in data else data.get("invalidRows")
    assert valid_rows == 1
    assert invalid_rows >= 4

    errors = data.get("errors", [])
    error_codes = {e.get("errorCode") or e.get("error_code") for e in errors}
    assert "INVALID_SEMESTER" in error_codes
    assert "DUPLICATE_IN_FILE" in error_codes
    assert "UNKNOWN_DEPARTMENT" in error_codes
    assert "INVALID_NAME" in error_codes

    batch_id = data.get("batch_id") or data.get("batchId")

    # Confirmation fails without skipInvalid=True (Task P4.7)
    resp_conf_fail = client.post(
        f"/api/v1/imports/{batch_id}/confirm", json={"skipInvalid": False}, headers=admin_headers
    )
    assert resp_conf_fail.status_code == 422
    assert resp_conf_fail.json()["error"]["code"] == "BATCH_HAS_ERRORS"

    # Confirmation succeeds with skipInvalid=True (Task P4.7)
    resp_conf_skip = client.post(
        f"/api/v1/imports/{batch_id}/confirm", json={"skipInvalid": True}, headers=admin_headers
    )
    assert resp_conf_skip.status_code == 200
    committed = (
        resp_conf_skip.json().get("committed_rows")
        if "committed_rows" in resp_conf_skip.json()
        else resp_conf_skip.json().get("committedRows")
    )
    assert committed == 1


# ==============================================================================
# 2. Subjects Import Tests
# ==============================================================================
def test_subject_import_direct_commit(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="sub_imp_admin@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    csv_content = (
        "subject_code,subject_name,department,semester,duration_minutes\n"
        "CS301,Data Structures,CSE,5,180\n"
        "CS302,Operating Systems,CSE,5,180\n"
        "CS303,Database Systems,CSE,5,180\n"
    )

    files = {"file": ("subjects.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/subjects/import?mode=commit", files=files, headers=admin_headers)
    assert resp.status_code == 200
    conf_data = resp.json()
    committed = (
        conf_data.get("committed_rows")
        if "committed_rows" in conf_data
        else conf_data.get("committedRows")
    )
    assert committed == 3

    # Verify subject in DB
    s1 = db_session.scalar(select(Subject).where(Subject.subject_code == "CS301"))
    assert s1 is not None
    assert s1.subject_name == "Data Structures"
    assert s1.default_duration_minutes == 180


# ==============================================================================
# 3. Enrollments Import Tests & Staleness Signaling
# ==============================================================================
def test_enrollments_import_and_staleness(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="enr_imp_admin@univ.edu")
    d_cse, _, cycle = setup_import_base_data(db_session, admin_headers)

    # First add a student and subject
    st = Student(
        student_number="S901",
        full_name="Student 901",
        department_id=d_cse.id,
        semester=5,
        status=EntityStatus.ACTIVE,
    )
    sub = Subject(
        subject_code="CS901",
        subject_name="Advanced Alg",
        department_id=d_cse.id,
        semester=5,
        status=EntityStatus.ACTIVE,
    )
    db_session.add_all([st, sub])
    db_session.commit()

    initial_version = cycle.data_version

    csv_content = "student_id,subject_code\nS901,CS901\n"

    files = {"file": ("enrollments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post(
        f"/api/v1/enrollments/import?cycleId={cycle.id}&mode=commit",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code == 200
    res_data = resp.json()
    committed = (
        res_data.get("committed_rows")
        if "committed_rows" in res_data
        else res_data.get("committedRows")
    )
    assert committed == 1

    # Verify staleness signaling: cycle data_version bumped (Task P4.10)
    db_session.refresh(cycle)
    assert cycle.data_version == initial_version + 1


def test_enrollment_prerequisites_check(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="enr_prereq@univ.edu")
    # Fresh DB session without any students or subjects:
    _, _, cycle = setup_import_base_data(db_session, admin_headers)

    # Empty students and subjects in this isolated cycle
    csv_content = "student_id,subject_code\nS1,C1\n"
    files = {"file": ("enr.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post(
        f"/api/v1/enrollments/import?cycleId={cycle.id}&mode=preview",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "PREREQUISITES_MISSING"


# ==============================================================================
# 4. File Safety & Edge Case Tests (Task P4.2)
# ==============================================================================
def test_csv_file_safety_checks(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="safety_admin@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    # 1. Non-UTF-8 binary file rejected
    binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    files = {"file": ("test.png", io.BytesIO(binary_content), "text/csv")}
    resp_bin = client.post(
        "/api/v1/students/import?mode=preview", files=files, headers=admin_headers
    )
    assert resp_bin.status_code == 422
    assert resp_bin.json()["error"]["code"] in ("INVALID_FILE_TYPE", "INVALID_ENCODING")

    # 2. UTF-8 BOM file accepted seamlessly
    bom_csv = "\ufeffstudent_id,student_name,department,semester\nS100,BOM Student,CSE,5\n"
    files_bom = {"file": ("bom.csv", io.BytesIO(bom_csv.encode("utf-8-sig")), "text/csv")}
    resp_bom = client.post(
        "/api/v1/students/import?mode=preview", files=files_bom, headers=admin_headers
    )
    assert resp_bom.status_code == 200
    valid_count = (
        resp_bom.json().get("valid_rows")
        if "valid_rows" in resp_bom.json()
        else resp_bom.json().get("validRows")
    )
    assert valid_count == 1

    # 3. Missing required columns rejected
    bad_csv = "random_col,other_col\n1,2\n"
    files_bad = {"file": ("bad.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    resp_bad = client.post(
        "/api/v1/students/import?mode=preview", files=files_bad, headers=admin_headers
    )
    assert resp_bad.status_code == 422
    assert resp_bad.json()["error"]["code"] == "MISSING_REQUIRED_COLUMNS"


def test_formula_injection_neutralization(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="formula_admin@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    # Name starting with formula prefix '=cmd'
    csv_content = "student_id,student_name,department,semester\nS999,=cmd|' /C calc'!A0,CSE,5\n"
    files = {"file": ("injection.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/students/import?mode=commit", files=files, headers=admin_headers)
    assert resp.status_code == 200

    # Verify neutralized with leading single quote in DB
    st = db_session.scalar(select(Student).where(Student.student_number == "S999"))
    assert st is not None
    assert st.full_name.startswith("'")


# ==============================================================================
# 5. Templates & Error CSV Download Tests (Task P4.6, P4.15)
# ==============================================================================
def test_templates_and_error_download(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="tpl_admin@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    # 1. Download templates
    for t in ["students", "subjects", "enrollments"]:
        resp = client.get(f"/api/v1/imports/templates/{t}", headers=admin_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert len(resp.text) > 20

    # 2. Download error report for a preview batch with errors
    bad_csv = "student_id,student_name,department,semester\nS888,Name,UNKNOWN_DEPT,bad_sem\n"
    files = {"file": ("err.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    resp_prev = client.post(
        "/api/v1/students/import?mode=preview", files=files, headers=admin_headers
    )
    batch_id = resp_prev.json().get("batch_id") or resp_prev.json().get("batchId")

    resp_err_csv = client.get(f"/api/v1/imports/{batch_id}/errors/download", headers=admin_headers)
    assert resp_err_csv.status_code == 200
    assert "text/csv" in resp_err_csv.headers["content-type"]
    assert "Row,Field,Value,Error Code" in resp_err_csv.text
    assert "UNKNOWN_DEPARTMENT" in resp_err_csv.text


def test_cancel_import_batch(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="cancel_admin@univ.edu")
    setup_import_base_data(db_session, admin_headers)

    csv_content = "student_id,student_name,department,semester\nS777,Cancel Test,CSE,5\n"
    files = {"file": ("cancel.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp_prev = client.post(
        "/api/v1/students/import?mode=preview", files=files, headers=admin_headers
    )
    batch_id = resp_prev.json().get("batch_id") or resp_prev.json().get("batchId")

    # Cancel batch
    resp_cancel = client.post(f"/api/v1/imports/{batch_id}/cancel", headers=admin_headers)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json().get("status") == ImportStatus.CANCELLED.value

    # Verify audit log
    audit_cancel = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == batch_id,
            AuditLog.action == AuditAction.IMPORT_CANCEL.value,
        )
    )
    assert audit_cancel is not None
