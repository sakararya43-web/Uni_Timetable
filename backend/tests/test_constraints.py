from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic import AcademicYear, Department, Student, Subject
from app.models.enums import CycleStatus, ScheduleStatus
from app.models.graph import ConflictEdge, ConflictGraphSnapshot
from app.models.schedule import ExamAssignment, ScheduleVersion
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot


def test_duplicate_enrollment_rejected(db_session: Session):
    """Enforces UNIQUE(student_id, subject_id, cycle_id) constraint (Task P2.3)."""
    # 1. Setup prerequisite entities
    dept = Department(code="CS", name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    year = AcademicYear(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31))
    db_session.add(year)
    db_session.flush()

    cycle = SchedulingCycle(
        academic_year_id=year.id,
        name="Cycle 1",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 20),
        timezone="UTC",
        status=CycleStatus.DRAFT,
    )
    db_session.add(cycle)
    db_session.flush()

    student = Student(
        student_number="STU_CONSTR_01", full_name="Student 1", department_id=dept.id, semester=5
    )
    subject = Subject(
        subject_code="CS101", subject_name="Intro to CS", department_id=dept.id, semester=5
    )
    db_session.add_all([student, subject])
    db_session.flush()

    # 2. Add first enrollment
    enr1 = Enrollment(student_id=student.id, subject_id=subject.id, cycle_id=cycle.id)
    db_session.add(enr1)
    db_session.flush()

    # 3. Add duplicate enrollment - must raise IntegrityError
    enr2 = Enrollment(student_id=student.id, subject_id=subject.id, cycle_id=cycle.id)
    db_session.add(enr2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_conflict_edge_self_loop_rejected(db_session: Session):
    """Enforces CHECK (exam_id_a < exam_id_b) rejecting self-loops and disordered pairs (Task P2.3)."""
    dept = Department(code="EE", name="Electrical Eng")
    db_session.add(dept)
    db_session.flush()

    year = AcademicYear(
        name="2026-2027-EE", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31)
    )
    db_session.add(year)
    db_session.flush()

    cycle = SchedulingCycle(
        academic_year_id=year.id,
        name="Cycle EE",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 20),
        timezone="UTC",
    )
    db_session.add(cycle)
    db_session.flush()

    sub = Subject(subject_code="EE201", subject_name="Circuits", department_id=dept.id, semester=3)
    db_session.add(sub)
    db_session.flush()

    exam = Exam(scheduling_cycle_id=cycle.id, subject_id=sub.id, duration_minutes=180)
    db_session.add(exam)
    db_session.flush()

    snapshot = ConflictGraphSnapshot(
        scheduling_cycle_id=cycle.id,
        version=1,
        vertex_count=1,
        edge_count=0,
        density=0.0,
        avg_degree=0.0,
        max_degree=0,
        enrollment_snapshot_hash="dummyhash",
    )
    db_session.add(snapshot)
    db_session.flush()

    # Self-loop: exam_id_a == exam_id_b -> must fail CHECK(exam_id_a < exam_id_b)
    self_edge = ConflictEdge(
        graph_snapshot_id=snapshot.id,
        exam_id_a=exam.id,
        exam_id_b=exam.id,
        shared_student_count=1,
    )
    db_session.add(self_edge)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_duplicate_exam_assignment_rejected(db_session: Session):
    """Enforces UNIQUE(schedule_version_id, exam_id) (Task P2.3, Hard Constraint 7)."""
    dept = Department(code="ME", name="Mechanical Eng")
    db_session.add(dept)
    db_session.flush()

    year = AcademicYear(
        name="2026-2027-ME", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31)
    )
    db_session.add(year)
    db_session.flush()

    cycle = SchedulingCycle(
        academic_year_id=year.id,
        name="Cycle ME",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 20),
        timezone="UTC",
    )
    db_session.add(cycle)
    db_session.flush()

    sub = Subject(
        subject_code="ME101", subject_name="Thermodynamics", department_id=dept.id, semester=1
    )
    db_session.add(sub)
    db_session.flush()

    exam = Exam(scheduling_cycle_id=cycle.id, subject_id=sub.id)
    slot1 = TimeSlot(
        scheduling_cycle_id=cycle.id,
        date=date(2026, 6, 10),
        start_time=date(2026, 6, 10),  # Will use time in real slot
        end_time=date(2026, 6, 10),
        duration_minutes=180,
        session_label="Morning",
        slot_index=0,
    )
    # Correct time slot types
    from datetime import time

    slot1.start_time = time(9, 0)
    slot1.end_time = time(12, 0)

    version = ScheduleVersion(
        scheduling_cycle_id=cycle.id,
        version_number=1,
        status=ScheduleStatus.CANDIDATE,
    )
    db_session.add_all([exam, slot1, version])
    db_session.flush()

    # Assign exam once
    assign1 = ExamAssignment(
        schedule_version_id=version.id,
        exam_id=exam.id,
        time_slot_id=slot1.id,
        color_id=0,
    )
    db_session.add(assign1)
    db_session.flush()

    # Assign the SAME exam a second time in the same schedule version
    assign2 = ExamAssignment(
        schedule_version_id=version.id,
        exam_id=exam.id,
        time_slot_id=slot1.id,
        color_id=1,
    )
    db_session.add(assign2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
