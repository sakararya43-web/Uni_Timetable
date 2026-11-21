"""
Idempotent Reference Data Seed Script for Academic Structure (Task P3.2).
Seeds initial departments, academic year, semesters, and programs.
"""

import logging
from datetime import date

from sqlalchemy import select

from app.config.database import SessionLocal
from app.models.academic import AcademicYear, Department, Program, Semester
from app.models.enums import CycleStatus, EntityStatus
from app.models.scheduling import SchedulingCycle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_academic")


def seed_academic_data() -> None:
    db = SessionLocal()
    try:
        # 1. Departments
        departments_data = [
            ("CSE", "Computer Science & Engineering"),
            ("EEE", "Electrical & Electronics Engineering"),
            ("ME", "Mechanical Engineering"),
        ]
        dept_map = {}
        for code, name in departments_data:
            dept = db.scalar(select(Department).where(Department.code == code))
            if not dept:
                dept = Department(code=code, name=name, status=EntityStatus.ACTIVE)
                db.add(dept)
                db.flush()
                logger.info(f"Created Department: {code} - {name}")
            else:
                logger.info(f"Department {code} already exists.")
            dept_map[code] = dept

        # 2. Academic Year
        ay_name = "2026-2027"
        ay = db.scalar(select(AcademicYear).where(AcademicYear.name == ay_name))
        if not ay:
            ay = AcademicYear(
                name=ay_name,
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 30),
                status=EntityStatus.ACTIVE,
            )
            db.add(ay)
            db.flush()
            logger.info(f"Created Academic Year: {ay_name}")
        else:
            logger.info(f"Academic Year {ay_name} already exists.")

        # 3. Semesters
        semesters_data = [
            ("Fall 2026", 1),
            ("Spring 2027", 2),
        ]
        sem_map = {}
        for name, num in semesters_data:
            sem = db.scalar(
                select(Semester).where(Semester.academic_year_id == ay.id, Semester.number == num)
            )
            if not sem:
                sem = Semester(
                    academic_year_id=ay.id,
                    name=name,
                    number=num,
                    status=EntityStatus.ACTIVE,
                )
                db.add(sem)
                db.flush()
                logger.info(f"Created Semester: {name} (Sem {num})")
            else:
                logger.info(f"Semester {name} already exists.")
            sem_map[num] = sem

        # 4. Programs
        programs_data = [
            ("CSE", "BTECH-CS", "B.Tech in Computer Science & Engineering"),
            ("EEE", "BTECH-EE", "B.Tech in Electrical & Electronics Engineering"),
            ("ME", "BTECH-ME", "B.Tech in Mechanical Engineering"),
        ]
        for dept_code, prog_code, prog_name in programs_data:
            dept = dept_map[dept_code]
            prog = db.scalar(
                select(Program).where(Program.department_id == dept.id, Program.code == prog_code)
            )
            if not prog:
                prog = Program(
                    department_id=dept.id,
                    code=prog_code,
                    name=prog_name,
                    status=EntityStatus.ACTIVE,
                )
                db.add(prog)
                db.flush()
                logger.info(f"Created Program: {prog_code} - {prog_name}")
            else:
                logger.info(f"Program {prog_code} already exists.")

        # 5. Sample Scheduling Cycle
        cycle_name = "Fall 2026 End-Term"
        cycle = db.scalar(select(SchedulingCycle).where(SchedulingCycle.name == cycle_name))
        if not cycle:
            cycle = SchedulingCycle(
                academic_year_id=ay.id,
                semester_id=sem_map[1].id,
                name=cycle_name,
                start_date=date(2026, 11, 1),
                end_date=date(2026, 11, 20),
                timezone="UTC",
                status=CycleStatus.DRAFT,
                configuration_json={
                    "sessions": [
                        {"code": "M", "name": "Morning", "start": "09:00", "end": "12:00"}
                    ],
                    "holidays": ["2026-11-08"],
                    "weekdays": [1, 2, 3, 4, 5],
                },
                data_version=1,
            )
            db.add(cycle)
            db.flush()
            logger.info(f"Created sample Scheduling Cycle: {cycle_name}")
        else:
            logger.info(f"Scheduling Cycle {cycle_name} already exists.")

        db.commit()
        logger.info("Academic reference data seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding academic data failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_academic_data()
