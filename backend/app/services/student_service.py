import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import check_department_scope, check_student_self_access
from app.middleware.error_handler import DomainException
from app.models.academic import Department, Student, Subject
from app.models.enums import AuditAction, EnrollmentStatus, EntityStatus, enum_val
from app.models.scheduling import Enrollment
from app.models.user import User
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.schemas.subject import SubjectResponse
from app.services.audit_service import audit_service


class StudentService:
    @staticmethod
    def get_students_paginated(
        db: Session,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        department_id: str | None = None,
        program_id: str | None = None,
        semester: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[StudentResponse], int, int]:
        effective_dept_id = department_id
        if actor.role == "coordinator":
            effective_dept_id = actor.department_id

        query = select(Student)
        if effective_dept_id:
            query = query.where(Student.department_id == effective_dept_id)
        if program_id:
            query = query.where(Student.program_id == program_id)
        if semester:
            query = query.where(Student.semester == semester)
        if status:
            query = query.where(Student.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                (Student.student_number.ilike(pattern)) | (Student.full_name.ilike(pattern))
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        students = list(
            db.scalars(
                query.order_by(Student.student_number.asc()).offset(offset).limit(page_size)
            ).all()
        )

        return [StudentResponse.model_validate(st) for st in students], total, total_pages

    @staticmethod
    def get_student_by_id(db: Session, student_id: str, actor: User) -> StudentResponse:
        st = db.get(Student, student_id)
        if not st:
            raise DomainException(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)

        if actor.role == "student":
            check_student_self_access(actor, st.user_id)
        else:
            check_department_scope(actor, st.department_id)

        return StudentResponse.model_validate(st)

    @staticmethod
    def create_student(
        db: Session, data: StudentCreate, actor: User, request_id: str | None = None
    ) -> StudentResponse:
        check_department_scope(actor, data.departmentId)

        # Unique immutable student_number (Task P3.9)
        existing = db.scalar(
            select(Student).where(Student.student_number == data.studentNumber.upper())
        )
        if existing:
            raise DomainException(
                code="DUPLICATE_STUDENT_NUMBER",
                message=f"Student number '{data.studentNumber}' already exists.",
                status_code=409,
            )

        dept = db.get(Department, data.departmentId)
        if not dept or dept.status != EntityStatus.ACTIVE:
            raise DomainException(
                code="UNKNOWN_DEPARTMENT",
                message=f"Department with ID '{data.departmentId}' does not exist or is archived.",
                status_code=422,
            )

        new_student = Student(
            student_number=data.studentNumber.upper(),
            full_name=data.fullName,
            email=data.email,
            department_id=data.departmentId,
            program_id=data.programId,
            semester=data.semester,
            status=EntityStatus.ACTIVE,
        )
        db.add(new_student)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.STUDENT_CREATE,
            entity_type="student",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=new_student.id,
            after={
                "student_number": new_student.student_number,
                "full_name": new_student.full_name,
                "department_id": new_student.department_id,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_student)

        return StudentResponse.model_validate(new_student)

    @staticmethod
    def update_student(
        db: Session,
        student_id: str,
        data: StudentUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> StudentResponse:
        st = db.get(Student, student_id)
        if not st:
            raise DomainException(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)

        check_department_scope(actor, st.department_id)

        before: dict[str, Any] = {
            "fullName": st.full_name,
            "departmentId": st.department_id,
            "status": enum_val(st.status),
        }

        if data.fullName is not None:
            st.full_name = data.fullName
        if data.email is not None:
            st.email = data.email
        if data.departmentId is not None:
            check_department_scope(actor, data.departmentId)
            st.department_id = data.departmentId
        if data.programId is not None:
            st.program_id = data.programId
        if data.semester is not None:
            st.semester = data.semester
        if data.status is not None:
            st.status = data.status

        audit_service.record(
            db=db,
            action=AuditAction.STUDENT_UPDATE,
            entity_type="student",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=st.id,
            before=before,
            after={
                "fullName": st.full_name,
                "departmentId": st.department_id,
                "status": enum_val(st.status),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(st)

        return StudentResponse.model_validate(st)

    @staticmethod
    def archive_student(
        db: Session, student_id: str, actor: User, request_id: str | None = None
    ) -> StudentResponse:
        st = db.get(Student, student_id)
        if not st:
            raise DomainException(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)

        check_department_scope(actor, st.department_id)

        st.status = EntityStatus.ARCHIVED

        audit_service.record(
            db=db,
            action=AuditAction.STUDENT_ARCHIVE,
            entity_type="student",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=st.id,
            after={"status": EntityStatus.ARCHIVED.value},
            request_id=request_id,
        )
        db.commit()
        db.refresh(st)

        return StudentResponse.model_validate(st)

    @staticmethod
    def get_student_subjects(
        db: Session, student_id: str, actor: User
    ) -> list[SubjectResponse]:
        """List of active subjects in which this student is enrolled (Task P3.10)."""
        st = db.get(Student, student_id)
        if not st:
            raise DomainException(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)

        if actor.role == "student":
            check_student_self_access(actor, st.user_id)
        else:
            check_department_scope(actor, st.department_id)

        query = (
            select(Subject)
            .join(Enrollment, Enrollment.subject_id == Subject.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        subjects = list(db.scalars(query.order_by(Subject.subject_code.asc())).all())

        return [SubjectResponse.model_validate(s) for s in subjects]


student_service = StudentService()
