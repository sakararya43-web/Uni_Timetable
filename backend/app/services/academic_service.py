import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import DomainException
from app.models.academic import AcademicYear, Department, Program, Semester
from app.models.enums import AuditAction, EntityStatus, enum_val
from app.models.user import User
from app.schemas.academic import (
    AcademicYearCreate,
    AcademicYearUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    ProgramCreate,
    ProgramUpdate,
    SemesterCreate,
    SemesterUpdate,
)
from app.services.audit_service import audit_service


class AcademicService:
    # ==========================================================================
    # Departments (FR-02)
    # ==========================================================================
    @staticmethod
    def get_departments(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Department], int, int]:
        query = select(Department)
        if status:
            query = query.where(Department.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where((Department.code.ilike(pattern)) | (Department.name.ilike(pattern)))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = list(
            db.scalars(
                query.order_by(Department.code.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total, total_pages

    @staticmethod
    def get_department_by_id(db: Session, dept_id: str) -> Department:
        dept = db.get(Department, dept_id)
        if not dept:
            raise DomainException(
                code="DEPARTMENT_NOT_FOUND", message="Department not found.", status_code=404
            )
        return dept

    @staticmethod
    def create_department(
        db: Session, data: DepartmentCreate, actor: User, request_id: str | None = None
    ) -> Department:
        existing = db.scalar(select(Department).where(Department.code == data.code.upper()))
        if existing:
            raise DomainException(
                code="DUPLICATE_DEPARTMENT_CODE",
                message=f"Department with code '{data.code}' already exists.",
                status_code=409,
            )

        dept = Department(code=data.code.upper(), name=data.name, status=EntityStatus.ACTIVE)
        db.add(dept)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_CREATE,
            entity_type="department",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=dept.id,
            after={"code": dept.code, "name": dept.name},
            request_id=request_id,
        )
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def update_department(
        db: Session,
        dept_id: str,
        data: DepartmentUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> Department:
        dept = db.get(Department, dept_id)
        if not dept:
            raise DomainException(
                code="DEPARTMENT_NOT_FOUND", message="Department not found.", status_code=404
            )

        before = {"name": dept.name, "status": enum_val(dept.status)}
        if data.name is not None:
            dept.name = data.name
        if data.status is not None:
            dept.status = data.status

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_UPDATE,
            entity_type="department",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=dept.id,
            before=before,
            after={"name": dept.name, "status": enum_val(dept.status)},
            request_id=request_id,
        )
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def archive_department(
        db: Session, dept_id: str, actor: User, request_id: str | None = None
    ) -> Department:
        dept = db.get(Department, dept_id)
        if not dept:
            raise DomainException(
                code="DEPARTMENT_NOT_FOUND", message="Department not found.", status_code=404
            )

        dept.status = EntityStatus.ARCHIVED
        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_ARCHIVE,
            entity_type="department",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=dept.id,
            after={"status": EntityStatus.ARCHIVED.value},
            request_id=request_id,
        )
        db.commit()
        db.refresh(dept)
        return dept

    # ==========================================================================
    # Academic Years (FR-02)
    # ==========================================================================
    @staticmethod
    def get_academic_years(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[AcademicYear], int, int]:
        query = select(AcademicYear)
        if status:
            query = query.where(AcademicYear.status == status)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = list(
            db.scalars(
                query.order_by(AcademicYear.start_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total, total_pages

    @staticmethod
    def get_academic_year_by_id(db: Session, year_id: str) -> AcademicYear:
        ay = db.get(AcademicYear, year_id)
        if not ay:
            raise DomainException(
                code="ACADEMIC_YEAR_NOT_FOUND", message="Academic year not found.", status_code=404
            )
        return ay

    @staticmethod
    def create_academic_year(
        db: Session,
        data: AcademicYearCreate,
        actor: User,
        request_id: str | None = None,
    ) -> AcademicYear:
        existing = db.scalar(select(AcademicYear).where(AcademicYear.name == data.name))
        if existing:
            raise DomainException(
                code="DUPLICATE_ACADEMIC_YEAR",
                message=f"Academic year '{data.name}' already exists.",
                status_code=409,
            )

        year = AcademicYear(
            name=data.name,
            start_date=data.startDate,
            end_date=data.endDate,
            status=EntityStatus.ACTIVE,
        )
        db.add(year)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_CREATE,
            entity_type="academic_year",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=year.id,
            after={
                "name": year.name,
                "start_date": str(year.start_date),
                "end_date": str(year.end_date),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(year)
        return year

    @staticmethod
    def update_academic_year(
        db: Session,
        year_id: str,
        data: AcademicYearUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> AcademicYear:
        ay = db.get(AcademicYear, year_id)
        if not ay:
            raise DomainException(
                code="ACADEMIC_YEAR_NOT_FOUND", message="Academic year not found.", status_code=404
            )

        before = {
            "name": ay.name,
            "start_date": str(ay.start_date),
            "end_date": str(ay.end_date),
            "status": enum_val(ay.status),
        }
        if data.name is not None:
            ay.name = data.name
        if data.startDate is not None:
            ay.start_date = data.startDate
        if data.endDate is not None:
            ay.end_date = data.endDate
        if data.status is not None:
            ay.status = data.status

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_UPDATE,
            entity_type="academic_year",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=ay.id,
            before=before,
            after={
                "name": ay.name,
                "start_date": str(ay.start_date),
                "end_date": str(ay.end_date),
                "status": enum_val(ay.status),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(ay)
        return ay

    @staticmethod
    def archive_academic_year(
        db: Session, year_id: str, actor: User, request_id: str | None = None
    ) -> AcademicYear:
        ay = db.get(AcademicYear, year_id)
        if not ay:
            raise DomainException(
                code="ACADEMIC_YEAR_NOT_FOUND", message="Academic year not found.", status_code=404
            )

        ay.status = EntityStatus.ARCHIVED
        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_ARCHIVE,
            entity_type="academic_year",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=ay.id,
            after={"status": EntityStatus.ARCHIVED.value},
            request_id=request_id,
        )
        db.commit()
        db.refresh(ay)
        return ay

    # ==========================================================================
    # Semesters (FR-02)
    # ==========================================================================
    @staticmethod
    def get_semesters(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        academic_year_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Semester], int, int]:
        query = select(Semester)
        if academic_year_id:
            query = query.where(Semester.academic_year_id == academic_year_id)
        if status:
            query = query.where(Semester.status == status)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = list(
            db.scalars(
                query.order_by(Semester.number.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total, total_pages

    @staticmethod
    def get_semester_by_id(db: Session, sem_id: str) -> Semester:
        sem = db.get(Semester, sem_id)
        if not sem:
            raise DomainException(
                code="SEMESTER_NOT_FOUND", message="Semester not found.", status_code=404
            )
        return sem

    @staticmethod
    def create_semester(
        db: Session, data: SemesterCreate, actor: User, request_id: str | None = None
    ) -> Semester:
        existing = db.scalar(
            select(Semester).where(
                Semester.academic_year_id == data.academicYearId,
                Semester.number == data.number,
            )
        )
        if existing:
            raise DomainException(
                code="DUPLICATE_SEMESTER",
                message=f"Semester number {data.number} already exists for this academic year.",
                status_code=409,
            )

        sem = Semester(
            academic_year_id=data.academicYearId,
            name=data.name,
            number=data.number,
            status=EntityStatus.ACTIVE,
        )
        db.add(sem)
        db.commit()
        db.refresh(sem)
        return sem

    @staticmethod
    def update_semester(
        db: Session,
        sem_id: str,
        data: SemesterUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> Semester:
        sem = db.get(Semester, sem_id)
        if not sem:
            raise DomainException(
                code="SEMESTER_NOT_FOUND", message="Semester not found.", status_code=404
            )

        if data.name is not None:
            sem.name = data.name
        if data.number is not None:
            sem.number = data.number
        if data.status is not None:
            sem.status = data.status

        db.commit()
        db.refresh(sem)
        return sem

    @staticmethod
    def archive_semester(
        db: Session, sem_id: str, actor: User, request_id: str | None = None
    ) -> Semester:
        sem = db.get(Semester, sem_id)
        if not sem:
            raise DomainException(
                code="SEMESTER_NOT_FOUND", message="Semester not found.", status_code=404
            )

        sem.status = EntityStatus.ARCHIVED
        db.commit()
        db.refresh(sem)
        return sem

    # ==========================================================================
    # Programs (FR-02)
    # ==========================================================================
    @staticmethod
    def get_programs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        department_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Program], int, int]:
        query = select(Program)
        if department_id:
            query = query.where(Program.department_id == department_id)
        if status:
            query = query.where(Program.status == status)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = list(
            db.scalars(
                query.order_by(Program.code.asc()).offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return items, total, total_pages

    @staticmethod
    def get_program_by_id(db: Session, prog_id: str) -> Program:
        prog = db.get(Program, prog_id)
        if not prog:
            raise DomainException(
                code="PROGRAM_NOT_FOUND", message="Program not found.", status_code=404
            )
        return prog

    @staticmethod
    def create_program(
        db: Session, data: ProgramCreate, actor: User, request_id: str | None = None
    ) -> Program:
        existing = db.scalar(select(Program).where(Program.code == data.code.upper()))
        if existing:
            raise DomainException(
                code="DUPLICATE_PROGRAM_CODE",
                message=f"Program code '{data.code}' already exists.",
                status_code=409,
            )

        prog = Program(
            department_id=data.departmentId,
            code=data.code.upper(),
            name=data.name,
            status=EntityStatus.ACTIVE,
        )
        db.add(prog)
        db.commit()
        db.refresh(prog)
        return prog

    @staticmethod
    def update_program(
        db: Session,
        prog_id: str,
        data: ProgramUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> Program:
        prog = db.get(Program, prog_id)
        if not prog:
            raise DomainException(
                code="PROGRAM_NOT_FOUND", message="Program not found.", status_code=404
            )

        if data.name is not None:
            prog.name = data.name
        if data.status is not None:
            prog.status = data.status

        db.commit()
        db.refresh(prog)
        return prog

    @staticmethod
    def archive_program(
        db: Session, prog_id: str, actor: User, request_id: str | None = None
    ) -> Program:
        prog = db.get(Program, prog_id)
        if not prog:
            raise DomainException(
                code="PROGRAM_NOT_FOUND", message="Program not found.", status_code=404
            )

        prog.status = EntityStatus.ARCHIVED
        db.commit()
        db.refresh(prog)
        return prog


academic_service = AcademicService()
