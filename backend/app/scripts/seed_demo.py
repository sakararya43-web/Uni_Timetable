"""Idempotent Demonstration Dataset Seeder (PRD §32, Task P16.3).

Seeds a complete university dataset demonstrating:
1. Two academic departments (CS & EE) and degree programs.
2. Four authenticated system users (Admin, Coordinator, Faculty, Student).
3. 50 synthetic students, 12 subjects across cohorts with realistic conflict density,
   including a dense hub exam (CS301) and an isolated exam (CS401).
4. Scheduling cycle (10–20 June 2026, Mon–Sat sessions, Morning & Afternoon, holidays).
5. Pre-generated deterministic time slots and initial conflict graph snapshot.

Refuses to execute in production environments.
"""

import logging
import os
import sys
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.settings import get_settings
from app.models.academic import AcademicYear, Department, Program, Semester, Student, Subject
from app.models.enums import AuditAction, CycleStatus, EntityStatus, RoleEnum, UserStatus
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot
from app.models.user import User
from app.services.audit_service import audit_service
from app.services.graph_service import graph_service
from app.services.slot_service import slot_service
from app.utils.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo")


def run_demo_seed(db: Session | None = None) -> dict[str, Any]:
    """Executes the demonstration dataset seed, returning a summary dictionary."""
    settings = get_settings()

    # Safety guard: refuse to run in production unless explicitly allowed
    app_env = getattr(settings, "APP_ENV", "development").lower()
    allow_seed = os.getenv("ALLOW_DEMO_SEED", "false").lower() in ["1", "true", "yes"]
    if app_env in ["prod", "production"] and not allow_seed:
        msg = "Demo data seeding skipped in production environment (set ALLOW_DEMO_SEED=true to seed)."
        logger.info(msg)
        return {"status": "skipped", "reason": msg}

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        logger.info("[seed_demo] Starting idempotent demo dataset population...")

        # -------------------------------------------------------------
        # 1. Departments & Programs (All 12 Academic Departments)
        # -------------------------------------------------------------
        all_depts_data = [
            (
                "CS",
                "Department of Computer Science",
                "BS-CS",
                "Bachelor of Science in Computer Science",
            ),
            (
                "EE",
                "Department of Electrical Engineering",
                "BS-EE",
                "Bachelor of Science in Electrical Engineering",
            ),
            (
                "ME",
                "Department of Mechanical Engineering",
                "BS-ME",
                "Bachelor of Science in Mechanical Engineering",
            ),
            (
                "CE",
                "Department of Civil & Environmental Engineering",
                "BS-CE",
                "Bachelor of Science in Civil Engineering",
            ),
            (
                "IT",
                "Department of Information Technology",
                "BS-IT",
                "Bachelor of Science in Information Technology",
            ),
            (
                "AI",
                "Department of Artificial Intelligence & Data Science",
                "BS-AI",
                "Bachelor of Science in Artificial Intelligence",
            ),
            (
                "BME",
                "Department of Biomedical Engineering",
                "BS-BME",
                "Bachelor of Science in Biomedical Engineering",
            ),
            (
                "CHE",
                "Department of Chemical Engineering",
                "BS-CHE",
                "Bachelor of Science in Chemical Engineering",
            ),
            (
                "MATH",
                "Department of Mathematics & Statistics",
                "BS-MATH",
                "Bachelor of Science in Mathematics",
            ),
            (
                "PHYS",
                "Department of Physics & Applied Sciences",
                "BS-PHYS",
                "Bachelor of Science in Physics",
            ),
            (
                "CHEM",
                "Department of Chemistry & Materials Science",
                "BS-CHEM",
                "Bachelor of Science in Chemistry",
            ),
            (
                "MGMT",
                "Department of Management & Business Studies",
                "BBA",
                "Bachelor of Business Administration",
            ),
        ]

        dept_map: dict[str, Department] = {}
        prog_map: dict[str, Program] = {}
        for d_code, d_name, p_code, p_name in all_depts_data:
            dept = db.scalar(select(Department).where(Department.code == d_code))
            if not dept:
                dept = Department(code=d_code, name=d_name, status=EntityStatus.ACTIVE)
                db.add(dept)
                db.flush()
            dept_map[d_code] = dept

            prog = db.scalar(select(Program).where(Program.code == p_code))
            if not prog:
                prog = Program(code=p_code, name=p_name, department_id=dept.id)
                db.add(prog)
                db.flush()
            prog_map[p_code] = prog

        dept_cs = dept_map["CS"]
        dept_ee = dept_map["EE"]
        prog_cs = prog_map["BS-CS"]
        prog_ee = prog_map["BS-EE"]

        # -------------------------------------------------------------
        # 2. Demo Authenticated Users (Admin, Coordinator, Faculty, Student)
        # -------------------------------------------------------------
        users_config = [
            ("admin@univ.edu", "AdminPass123!", "System Administrator", RoleEnum.ADMIN, dept_cs.id),
            (
                "coordinator@univ.edu",
                "CoordPass123!",
                "Academic Coordinator",
                RoleEnum.COORDINATOR,
                dept_cs.id,
            ),
            (
                "faculty@univ.edu",
                "FacultyPass123!",
                "Professor Faculty",
                RoleEnum.FACULTY,
                dept_cs.id,
            ),
            ("student@univ.edu", "StudentPass123!", "Student User", RoleEnum.STUDENT, dept_cs.id),
        ]
        user_entities: dict[str, User] = {}
        for email, pwd, full_name, role, dept_id in users_config:
            u = db.scalar(select(User).where(User.email == email))
            if not u:
                u = User(
                    email=email,
                    password_hash=hash_password(pwd),
                    full_name=full_name,
                    role=role,
                    department_id=dept_id,
                    status=UserStatus.ACTIVE,
                )
                db.add(u)
                db.flush()
                audit_service.record(
                    db=db,
                    action=AuditAction.USER_CREATE,
                    entity_type="user",
                    actor_email="system_demo_seed",
                    entity_id=u.id,
                    after={"email": email, "role": role.value, "seeded_demo": True},
                )
            user_entities[email] = u

        student_user = user_entities["student@univ.edu"]

        # -------------------------------------------------------------
        # 3. Academic Year & Semester
        # -------------------------------------------------------------
        ay_name = "2025-2026 Demo AY"
        ay = db.scalar(select(AcademicYear).where(AcademicYear.name == ay_name))
        if not ay:
            ay = AcademicYear(
                name=ay_name,
                start_date=date(2025, 9, 1),
                end_date=date(2026, 6, 30),
                status=EntityStatus.ACTIVE,
            )
            db.add(ay)
            db.flush()

        sem = db.scalar(
            select(Semester).where(Semester.academic_year_id == ay.id, Semester.number == 2)
        )
        if not sem:
            sem = Semester(
                academic_year_id=ay.id,
                name="Spring 2026",
                number=2,
                status=EntityStatus.ACTIVE,
            )
            db.add(sem)
            db.flush()

        # -------------------------------------------------------------
        # 4. Subjects (23 realistic courses across all 12 departments)
        # -------------------------------------------------------------
        subjects_data = [
            ("CS101", "Introduction to Programming", dept_cs.id, prog_cs.id, 1, 3.0),
            ("CS102", "Discrete Mathematics", dept_cs.id, prog_cs.id, 1, 3.0),
            ("CS201", "Data Structures & Algorithms", dept_cs.id, prog_cs.id, 2, 4.0),
            ("CS202", "Computer Organization & Architecture", dept_cs.id, prog_cs.id, 2, 3.0),
            ("CS301", "Operating Systems & Concurrency", dept_cs.id, prog_cs.id, 3, 4.0),
            ("CS302", "Database Management Systems", dept_cs.id, prog_cs.id, 3, 3.0),
            ("CS303", "Computer Networks & Protocols", dept_cs.id, prog_cs.id, 3, 3.0),
            ("CS401", "Advanced Machine Learning Capstone", dept_cs.id, prog_cs.id, 4, 3.0),
            ("EE101", "Linear Circuit Analysis", dept_ee.id, prog_ee.id, 1, 3.0),
            ("EE102", "Digital Logic & Microprocessors", dept_ee.id, prog_ee.id, 1, 3.0),
            ("EE201", "Signals and Linear Systems", dept_ee.id, prog_ee.id, 2, 3.0),
            ("EE202", "Electromagnetic Fields & Waves", dept_ee.id, prog_ee.id, 2, 3.0),
            (
                "ME101",
                "Engineering Mechanics & Statics",
                dept_map["ME"].id,
                prog_map["BS-ME"].id,
                1,
                3.0,
            ),
            (
                "ME201",
                "Thermodynamics & Fluid Dynamics",
                dept_map["ME"].id,
                prog_map["BS-ME"].id,
                2,
                4.0,
            ),
            (
                "CE101",
                "Structural Analysis & Materials",
                dept_map["CE"].id,
                prog_map["BS-CE"].id,
                1,
                3.0,
            ),
            (
                "IT101",
                "Cloud Infrastructure & Distributed Systems",
                dept_map["IT"].id,
                prog_map["BS-IT"].id,
                2,
                3.0,
            ),
            (
                "AI101",
                "Machine Learning & Neural Networks",
                dept_map["AI"].id,
                prog_map["BS-AI"].id,
                3,
                4.0,
            ),
            (
                "BME101",
                "Biomedical Instrumentation & Sensors",
                dept_map["BME"].id,
                prog_map["BS-BME"].id,
                2,
                3.0,
            ),
            (
                "CHE101",
                "Chemical Reaction Engineering",
                dept_map["CHE"].id,
                prog_map["BS-CHE"].id,
                2,
                3.0,
            ),
            (
                "MATH101",
                "Linear Algebra & Advanced Calculus",
                dept_map["MATH"].id,
                prog_map["BS-MATH"].id,
                1,
                4.0,
            ),
            (
                "PHYS101",
                "Classical & Quantum Physics",
                dept_map["PHYS"].id,
                prog_map["BS-PHYS"].id,
                1,
                3.0,
            ),
            (
                "CHEM101",
                "General & Physical Chemistry",
                dept_map["CHEM"].id,
                prog_map["BS-CHEM"].id,
                1,
                3.0,
            ),
            (
                "MGMT101",
                "Principles of Management & Economics",
                dept_map["MGMT"].id,
                prog_map["BBA"].id,
                1,
                3.0,
            ),
        ]
        subject_map: dict[str, Subject] = {}
        for code, name, d_id, p_id, sem_num, credits in subjects_data:
            s = db.scalar(select(Subject).where(Subject.subject_code == code))
            if not s:
                s = Subject(
                    subject_code=code,
                    subject_name=name,
                    department_id=d_id,
                    program_id=p_id,
                    semester=sem_num,
                    credits=credits,
                    status=EntityStatus.ACTIVE,
                )
                db.add(s)
                db.flush()
            subject_map[code] = s

        # -------------------------------------------------------------
        # 5. Students (50 students: 30 CS, 20 EE)
        # -------------------------------------------------------------
        student_map: dict[str, Student] = {}
        # CS Students
        for i in range(1, 31):
            s_num = f"CS-{i:03d}"
            s_name = f"Synthetic Student CS {i:02d}"
            s_email = f"student.cs{i:02d}@univ.edu"
            sem_val = 1 if i <= 10 else (2 if i <= 20 else 3)
            # Link CS-001 to student_user
            u_id = student_user.id if i == 1 else None
            if i == 1:
                s_email = "student@univ.edu"

            stu = db.scalar(select(Student).where(Student.student_number == s_num))
            if not stu:
                stu = Student(
                    student_number=s_num,
                    full_name=s_name,
                    email=s_email,
                    department_id=dept_cs.id,
                    program_id=prog_cs.id,
                    semester=sem_val,
                    user_id=u_id,
                    status=EntityStatus.ACTIVE,
                )
                db.add(stu)
                db.flush()
            elif i == 1 and stu.user_id != student_user.id:
                stu.user_id = student_user.id
                db.flush()
            student_map[s_num] = stu

        # EE Students
        for i in range(1, 21):
            s_num = f"EE-{i:03d}"
            s_name = f"Synthetic Student EE {i:02d}"
            s_email = f"student.ee{i:02d}@univ.edu"
            sem_val = 1 if i <= 10 else 2

            stu = db.scalar(select(Student).where(Student.student_number == s_num))
            if not stu:
                stu = Student(
                    student_number=s_num,
                    full_name=s_name,
                    email=s_email,
                    department_id=dept_ee.id,
                    program_id=prog_ee.id,
                    semester=sem_val,
                    status=EntityStatus.ACTIVE,
                )
                db.add(stu)
                db.flush()
            student_map[s_num] = stu

        # Other Department Students (2 students per department)
        other_depts_config = [
            ("ME", "BS-ME"),
            ("CE", "BS-CE"),
            ("IT", "BS-IT"),
            ("AI", "BS-AI"),
            ("BME", "BS-BME"),
            ("CHE", "BS-CHE"),
            ("MATH", "BS-MATH"),
            ("PHYS", "BS-PHYS"),
            ("CHEM", "BS-CHEM"),
            ("MGMT", "BBA"),
        ]
        for d_code, p_code in other_depts_config:
            for k in range(1, 3):
                s_num = f"{d_code}-{k:03d}"
                s_name = f"Synthetic Student {d_code} {k:02d}"
                s_email = f"student.{d_code.lower()}{k:02d}@univ.edu"
                sem_val = 1 if k == 1 else 2

                stu = db.scalar(select(Student).where(Student.student_number == s_num))
                if not stu:
                    stu = Student(
                        student_number=s_num,
                        full_name=s_name,
                        email=s_email,
                        department_id=dept_map[d_code].id,
                        program_id=prog_map[p_code].id,
                        semester=sem_val,
                        status=EntityStatus.ACTIVE,
                    )
                    db.add(stu)
                    db.flush()
                student_map[s_num] = stu

        # -------------------------------------------------------------
        # 6. Pre-configured Scheduling Cycle (10–20 June 2026)
        # -------------------------------------------------------------
        cycle_name = "June 2026 Demo Final Exams"
        cycle = db.scalar(select(SchedulingCycle).where(SchedulingCycle.name == cycle_name))
        special_restrictions: list[dict[str, Any]] = []
        cycle_cfg: dict[str, Any] = {
            "sessions": [
                {"label": "Morning", "startTime": "09:00", "endTime": "12:00", "enabled": True},
                {"label": "Afternoon", "startTime": "14:00", "endTime": "17:00", "enabled": True},
            ],
            "examDaysOfWeek": [1, 2, 3, 4, 5, 6],  # Mon - Sat
            "holidays": ["2026-06-15"],  # University Holiday
            "maxExamsPerSession": 4,
            "specialRestrictions": special_restrictions,
        }

        if not cycle:
            cycle = SchedulingCycle(
                academic_year_id=ay.id,
                semester_id=sem.id,
                name=cycle_name,
                start_date=date(2026, 6, 10),
                end_date=date(2026, 6, 20),
                timezone="UTC",
                status=CycleStatus.DRAFT,
                configuration_json=cycle_cfg,
                data_version=1,
            )
            db.add(cycle)
            db.flush()

        # -------------------------------------------------------------
        # 7. Time Slots (Generated deterministically from cycle config)
        # -------------------------------------------------------------
        existing_slots = list(
            db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle.id)).all()
        )
        if not existing_slots:
            raw_slots = slot_service.generate_slots(cycle.start_date, cycle.end_date, cycle_cfg)
            for s_dict in raw_slots:
                ts = TimeSlot(
                    scheduling_cycle_id=cycle.id,
                    date=s_dict["date"],
                    start_time=s_dict["start_time"],
                    end_time=s_dict["end_time"],
                    duration_minutes=s_dict["duration_minutes"],
                    session_label=s_dict["session_label"],
                    slot_index=s_dict["slot_index"],
                    capacity=s_dict.get("capacity"),
                    enabled=s_dict.get("enabled", True),
                )
                db.add(ts)
            db.flush()

        # -------------------------------------------------------------
        # 8. Exams for the Cycle
        # -------------------------------------------------------------
        exam_map: dict[str, Exam] = {}
        for code, sub in subject_map.items():
            ex = db.scalar(
                select(Exam).where(Exam.scheduling_cycle_id == cycle.id, Exam.subject_id == sub.id)
            )
            if not ex:
                ex = Exam(
                    scheduling_cycle_id=cycle.id,
                    subject_id=sub.id,
                    duration_minutes=180,
                    status=EntityStatus.ACTIVE,
                )
                db.add(ex)
                db.flush()
            exam_map[code] = ex

        # -------------------------------------------------------------
        # 9. Enrollments (Reflecting realistic cohorts & cross-listed subjects)
        # -------------------------------------------------------------
        enrollments_to_add: list[tuple[str, str]] = []

        # CS Cohort 1
        for i in range(1, 11):
            s_num = f"CS-{i:03d}"
            enrollments_to_add.extend([(s_num, "CS101"), (s_num, "CS102"), (s_num, "EE102")])

        # CS Cohort 2
        for i in range(11, 21):
            s_num = f"CS-{i:03d}"
            enrollments_to_add.extend([(s_num, "CS201"), (s_num, "CS202"), (s_num, "EE201")])

        # CS Cohort 3 (High-degree hub on CS301)
        for i in range(21, 31):
            s_num = f"CS-{i:03d}"
            enrollments_to_add.extend([(s_num, "CS301"), (s_num, "CS302"), (s_num, "CS303")])
            if i in [21, 22]:
                enrollments_to_add.append(
                    (s_num, "CS101")
                )  # Repeaters bridging Cohort 3 and Cohort 1

        # EE Cohort 1 (Cross-department enrollments bridging CS101 and EE101)
        for i in range(1, 11):
            s_num = f"EE-{i:03d}"
            enrollments_to_add.extend([(s_num, "EE101"), (s_num, "EE102"), (s_num, "CS101")])

        # EE Cohort 2 (Cross-department bridge to CS301)
        for i in range(11, 21):
            s_num = f"EE-{i:03d}"
            enrollments_to_add.extend([(s_num, "EE201"), (s_num, "EE202"), (s_num, "CS301")])

        # Single enrollment for near-isolated CS401
        enrollments_to_add.append(("CS-001", "CS401"))

        # Enrollments for other department students across cohorts
        enrollments_to_add.extend(
            [
                ("ME-001", "ME101"),
                ("ME-001", "MATH101"),
                ("ME-002", "ME201"),
                ("ME-002", "MATH101"),
                ("CE-001", "CE101"),
                ("CE-001", "PHYS101"),
                ("CE-002", "CE101"),
                ("CE-002", "MATH101"),
                ("IT-001", "IT101"),
                ("IT-001", "CS101"),
                ("IT-002", "IT101"),
                ("IT-002", "CS201"),
                ("AI-001", "AI101"),
                ("AI-001", "CS201"),
                ("AI-002", "AI101"),
                ("AI-002", "MATH101"),
                ("BME-001", "BME101"),
                ("BME-001", "CHEM101"),
                ("BME-002", "BME101"),
                ("BME-002", "EE101"),
                ("CHE-001", "CHE101"),
                ("CHE-001", "CHEM101"),
                ("CHE-002", "CHE101"),
                ("CHE-002", "MATH101"),
                ("MATH-001", "MATH101"),
                ("MATH-001", "CS102"),
                ("MATH-002", "MATH101"),
                ("MATH-002", "PHYS101"),
                ("PHYS-001", "PHYS101"),
                ("PHYS-001", "MATH101"),
                ("PHYS-002", "PHYS101"),
                ("PHYS-002", "EE101"),
                ("CHEM-001", "CHEM101"),
                ("CHEM-001", "CHE101"),
                ("CHEM-002", "CHEM101"),
                ("CHEM-002", "PHYS101"),
                ("MGMT-001", "MGMT101"),
                ("MGMT-001", "CS101"),
                ("MGMT-002", "MGMT101"),
                ("MGMT-002", "CS102"),
            ]
        )

        added_enr_count = 0
        for s_num, code in enrollments_to_add:
            stu = student_map[s_num]
            sub = subject_map[code]
            existing_enr = db.scalar(
                select(Enrollment).where(
                    Enrollment.cycle_id == cycle.id,
                    Enrollment.student_id == stu.id,
                    Enrollment.subject_id == sub.id,
                )
            )
            if not existing_enr:
                enr = Enrollment(student_id=stu.id, subject_id=sub.id, cycle_id=cycle.id)
                db.add(enr)
                added_enr_count += 1
        db.flush()

        # -------------------------------------------------------------
        # 10. Pre-build Initial Conflict Graph Snapshot
        # -------------------------------------------------------------
        admin_actor = user_entities["admin@univ.edu"]
        snapshot, is_new, val = graph_service.build_graph_snapshot(
            db=db,
            cycle_id=cycle.id,
            actor=admin_actor,
            force=True,
        )

        db.commit()

        summary = {
            "departments": len(dept_map),
            "programs": len(prog_map),
            "users": len(users_config),
            "subjects": len(subject_map),
            "students": len(student_map),
            "enrollments_added": added_enr_count,
            "cycle_id": cycle.id,
            "cycle_name": cycle.name,
            "graph_snapshot_id": snapshot.id,
            "graph_version": snapshot.version,
            "isolated_subjects": ["CS401"],
            "hub_subject": "CS301",
        }
        logger.info(f"[seed_demo] Seeding completed successfully: {summary}")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"[seed_demo] Seeding failed: {e}")
        raise
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    try:
        run_demo_seed()
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
