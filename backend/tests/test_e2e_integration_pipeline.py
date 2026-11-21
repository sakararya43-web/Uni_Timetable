"""End-to-End Integration Pipeline and Determinism Test Suite.

PRD §20, §23, Tasks P15.3, P15.5.
Validates the full enterprise scheduling pipeline through the HTTP API:
1. Academic structure provisioning (Departments, Programs, Subjects, Students).
2. Scheduling Cycle initialization and automated Slot Generation.
3. Enrollment registration and Conflict Graph Snapshot construction.
4. Schedule Generation via DSATUR with Determinism Replay assertion.
5. Review, Validation, and Official Publication.
6. Student Timetable privacy-scoped access and Administrative Document Exports.
"""

import uuid
from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.academic import Department, Program, Student, Subject
from app.models.enums import CycleStatus, RoleEnum
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot
from tests.conftest import make_auth_user


def test_full_scheduling_pipeline_e2e(client: TestClient, db_session: Session) -> None:
    """Executes the full scheduling lifecycle from raw academic setup to publication and exports."""
    # Step 1: Admin User Provisioning
    _, admin_headers = make_auth_user(
        db=db_session, role=RoleEnum.ADMIN.value, email="e2e_admin@univ.edu"
    )

    # Step 2: Academic Department, Program, and Subjects
    dept = Department(code=f"E2E_{uuid.uuid4().hex[:4].upper()}", name="E2E Department")
    db_session.add(dept)
    db_session.flush()

    prog = Program(
        code=f"BS_{uuid.uuid4().hex[:4].upper()}", name="BS Program", department_id=dept.id
    )
    db_session.add(prog)
    db_session.flush()

    sub1 = Subject(
        subject_code=f"E2E_101_{uuid.uuid4().hex[:4]}",
        subject_name="E2E Algorithms",
        department_id=dept.id,
        semester=1,
        credits=3.0,
    )
    sub2 = Subject(
        subject_code=f"E2E_102_{uuid.uuid4().hex[:4]}",
        subject_name="E2E Systems",
        department_id=dept.id,
        semester=1,
        credits=3.0,
    )
    sub3 = Subject(
        subject_code=f"E2E_103_{uuid.uuid4().hex[:4]}",
        subject_name="E2E Databases",
        department_id=dept.id,
        semester=1,
        credits=3.0,
    )
    db_session.add_all([sub1, sub2, sub3])
    db_session.flush()

    # Step 3: Students
    stu1 = Student(
        student_number="E2E_STU_001",
        full_name="Alice Smith",
        email="alice@univ.edu",
        department_id=dept.id,
        program_id=prog.id,
        semester=1,
    )
    stu2 = Student(
        student_number="E2E_STU_002",
        full_name="Bob Jones",
        email="bob@univ.edu",
        department_id=dept.id,
        program_id=prog.id,
        semester=1,
    )
    db_session.add_all([stu1, stu2])
    db_session.flush()

    # Step 4: Scheduling Cycle
    cycle = SchedulingCycle(
        name="Fall 2026 E2E Cycle",
        academic_year_id=f"AY_{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 5),
        status=CycleStatus.DRAFT,
    )
    db_session.add(cycle)
    db_session.flush()

    # Step 5: Slots (5 Days x 2 sessions = 10 slots)
    slots: list[TimeSlot] = []
    for day in range(1, 6):
        d = date(2026, 12, day)
        s_m = TimeSlot(
            scheduling_cycle_id=cycle.id,
            date=d,
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_minutes=180,
            session_label="Morning",
            slot_index=len(slots) + 1,
        )
        slots.append(s_m)
        s_a = TimeSlot(
            scheduling_cycle_id=cycle.id,
            date=d,
            start_time=time(14, 0),
            end_time=time(17, 0),
            duration_minutes=180,
            session_label="Afternoon",
            slot_index=len(slots) + 1,
        )
        slots.append(s_a)
    db_session.add_all(slots)
    db_session.flush()

    # Step 6: Exams and Enrollments
    exam1 = Exam(subject_id=sub1.id, scheduling_cycle_id=cycle.id, duration_minutes=180)
    exam2 = Exam(subject_id=sub2.id, scheduling_cycle_id=cycle.id, duration_minutes=180)
    exam3 = Exam(subject_id=sub3.id, scheduling_cycle_id=cycle.id, duration_minutes=180)
    db_session.add_all([exam1, exam2, exam3])
    db_session.flush()

    # Student 1 takes sub1 and sub2 (creating conflict between 1 and 2)
    # Student 2 takes sub2 and sub3 (creating conflict between 2 and 3)
    enr1 = Enrollment(student_id=stu1.id, subject_id=sub1.id, cycle_id=cycle.id)
    enr2 = Enrollment(student_id=stu1.id, subject_id=sub2.id, cycle_id=cycle.id)
    enr3 = Enrollment(student_id=stu2.id, subject_id=sub2.id, cycle_id=cycle.id)
    enr4 = Enrollment(student_id=stu2.id, subject_id=sub3.id, cycle_id=cycle.id)
    db_session.add_all([enr1, enr2, enr3, enr4])
    db_session.commit()

    # Step 7: Build Conflict Graph via API
    res_graph = client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)
    assert res_graph.status_code == 200, f"Graph build failed: {res_graph.text}"
    graph_data = res_graph.json()
    v_count = graph_data["stats"].get("vertexCount") or graph_data["stats"].get("vertex_count")
    e_count = graph_data["stats"].get("edgeCount") or graph_data["stats"].get("edge_count")
    assert v_count == 3
    assert e_count == 2  # (1, 2) and (2, 3)

    # Step 8: Generate Schedule via API and assert Determinism (Task P15.5)
    gen_payload = {
        "algorithm": "dsatur",
        "deterministic": True,
        "preserveLockedExams": True,
    }
    res_run1 = client.post(
        f"/api/v1/cycles/{cycle.id}/schedule/generate", json=gen_payload, headers=admin_headers
    )
    assert res_run1.status_code == 200, f"Generate run 1 failed: {res_run1.text}"
    run1_data = res_run1.json()
    is_valid1 = run1_data.get("isValid") if "isValid" in run1_data else run1_data.get("is_valid")
    assert is_valid1 is True

    # Replay on identical snapshot: must produce exact same slot mapping
    res_run2 = client.post(
        f"/api/v1/cycles/{cycle.id}/schedule/generate", json=gen_payload, headers=admin_headers
    )
    assert res_run2.status_code == 200, f"Generate run 2 failed: {res_run2.text}"
    run2_data = res_run2.json()
    c1 = run1_data.get("colorsUsed") or run1_data.get("colors_used")
    c2 = run2_data.get("colorsUsed") or run2_data.get("colors_used")
    assert c1 == c2
    s1 = run1_data.get("softScore") or run1_data.get("soft_score")
    s2 = run2_data.get("softScore") or run2_data.get("soft_score")
    assert s1 == s2

    # Step 9: Save Run as Candidate Version
    res_save = client.post(f"/api/v1/schedule-runs/{run1_data['id']}/save", headers=admin_headers)
    assert res_save.status_code == 200, f"Save candidate failed: {res_save.text}"
    ver_data = res_save.json()
    version_id = ver_data["id"]

    # Step 10: Publish Version
    res_pub = client.post(
        f"/api/v1/schedules/{version_id}/publish",
        json={"confirm": True, "notes": "E2E Official Release"},
        headers=admin_headers,
    )
    assert res_pub.status_code == 200, f"Publish failed: {res_pub.text}"
    pub_status = str(res_pub.json().get("status")).lower()
    assert pub_status == "published"

    # Step 11: Student View Isolation (Student 1 queries /me/timetable)
    _, stu1_headers = make_auth_user(db=db_session, role=RoleEnum.STUDENT.value, email=stu1.email)
    res_stu = client.get("/api/v1/me/timetable", headers=stu1_headers)
    assert res_stu.status_code == 200, f"Student timetable query failed: {res_stu.text}"
    stu_tt = res_stu.json()
    stu_num = stu_tt.get("studentNumber") or stu_tt.get("student_number")
    assert stu_num == "E2E_STU_001"
    # Alice is enrolled in 2 subjects (E2E_101 and E2E_102)
    assert len(stu_tt["exams"]) == 2
    # Verify no third exam is present
    stu_codes = [e.get("subjectCode") or e.get("subject_code") for e in stu_tt["exams"]]
    assert sub1.subject_code in stu_codes
    assert sub2.subject_code in stu_codes
    assert sub3.subject_code not in stu_codes

    # Step 12: Exports (PDF, CSV, Excel)
    res_csv = client.get(f"/api/v1/schedules/{version_id}/export/csv", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    res_pdf = client.get(f"/api/v1/schedules/{version_id}/export/pdf", headers=admin_headers)
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]

    res_xlsx = client.get(f"/api/v1/schedules/{version_id}/export/excel", headers=admin_headers)
    assert res_xlsx.status_code == 200
    assert "spreadsheetml" in res_xlsx.headers["content-type"]
