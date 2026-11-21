import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import check_department_scope
from app.middleware.error_handler import DomainException
from app.models.academic import Department, Student, Subject
from app.models.enums import AuditAction, EnrollmentStatus, EntityStatus, enum_val
from app.models.graph import ConflictGraphSnapshot
from app.models.scheduling import Enrollment, Exam
from app.models.user import User
from app.schemas.student import StudentResponse
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.audit_service import audit_service


class SubjectService:
    @staticmethod
    def get_subjects_paginated(
        db: Session,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        department_id: str | None = None,
        program_id: str | None = None,
        semester: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[SubjectResponse], int, int]:
        # Enforce department scoping for coordinators
        effective_dept_id = department_id
        if actor.role == "coordinator":
            effective_dept_id = actor.department_id

        query = select(Subject)
        if effective_dept_id:
            query = query.where(Subject.department_id == effective_dept_id)
        if program_id:
            query = query.where(Subject.program_id == program_id)
        if semester:
            query = query.where(Subject.semester == semester)
        if status:
            query = query.where(Subject.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                (Subject.subject_code.ilike(pattern)) | (Subject.subject_name.ilike(pattern))
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        subjects = list(
            db.scalars(
                query.order_by(Subject.subject_code.asc()).offset(offset).limit(page_size)
            ).all()
        )

        # Compute derived enrollment counts via query (FR-03, Task P3.5)
        subject_responses: list[SubjectResponse] = []
        for s in subjects:
            enr_count = (
                db.scalar(
                    select(func.count(Enrollment.id)).where(
                        Enrollment.subject_id == s.id,
                        Enrollment.status == EnrollmentStatus.ACTIVE,
                    )
                )
                or 0
            )
            deg_val: int | None = None
            exam = db.scalar(
                select(Exam)
                .join(
                    ConflictGraphSnapshot,
                    ConflictGraphSnapshot.scheduling_cycle_id == Exam.scheduling_cycle_id,
                )
                .where(Exam.subject_id == s.id)
                .order_by(ConflictGraphSnapshot.version.desc())
                .limit(1)
            )
            if exam:
                snap = db.scalar(
                    select(ConflictGraphSnapshot)
                    .where(ConflictGraphSnapshot.scheduling_cycle_id == exam.scheduling_cycle_id)
                    .order_by(ConflictGraphSnapshot.version.desc())
                    .limit(1)
                )
                if snap and snap.graph_data_json:
                    adj = snap.graph_data_json.get("adjacency", {})
                    deg_val = len(adj.get(exam.id, []))

            resp = SubjectResponse(
                id=s.id,
                subject_code=s.subject_code,
                subject_name=s.subject_name,
                department_id=s.department_id,
                program_id=s.program_id,
                semester=s.semester,
                credits=s.credits,
                default_duration_minutes=s.default_duration_minutes,
                priority=s.priority,
                preferred_dates=s.preferred_dates or [],
                restricted_dates=s.restricted_dates or [],
                status=s.status,
                enrollment_count=enr_count,
                conflict_degree=deg_val,
                scheduling_status=None,
            )
            subject_responses.append(resp)

        return subject_responses, total, total_pages

    @staticmethod
    def get_subject_by_id(db: Session, subject_id: str, actor: User) -> SubjectResponse:
        s = db.get(Subject, subject_id)
        if not s:
            raise DomainException(
                code="SUBJECT_NOT_FOUND", message="Subject not found.", status_code=404
            )

        check_department_scope(actor, s.department_id)

        enr_count = (
            db.scalar(
                select(func.count(Enrollment.id)).where(
                    Enrollment.subject_id == s.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
            or 0
        )

        deg_val: int | None = None
        exam = db.scalar(
            select(Exam)
            .join(
                ConflictGraphSnapshot,
                ConflictGraphSnapshot.scheduling_cycle_id == Exam.scheduling_cycle_id,
            )
            .where(Exam.subject_id == s.id)
            .order_by(ConflictGraphSnapshot.version.desc())
            .limit(1)
        )
        if exam:
            snap = db.scalar(
                select(ConflictGraphSnapshot)
                .where(ConflictGraphSnapshot.scheduling_cycle_id == exam.scheduling_cycle_id)
                .order_by(ConflictGraphSnapshot.version.desc())
                .limit(1)
            )
            if snap and snap.graph_data_json:
                adj = snap.graph_data_json.get("adjacency", {})
                deg_val = len(adj.get(exam.id, []))

        return SubjectResponse(
            id=s.id,
            subject_code=s.subject_code,
            subject_name=s.subject_name,
            department_id=s.department_id,
            program_id=s.program_id,
            semester=s.semester,
            credits=s.credits,
            default_duration_minutes=s.default_duration_minutes,
            priority=s.priority,
            preferred_dates=s.preferred_dates or [],
            restricted_dates=s.restricted_dates or [],
            status=s.status,
            enrollment_count=enr_count,
            conflict_degree=deg_val,
            scheduling_status=None,
        )

    @staticmethod
    def create_subject(
        db: Session, data: SubjectCreate, actor: User, request_id: str | None = None
    ) -> SubjectResponse:
        check_department_scope(actor, data.departmentId)

        # Check unique code globally (ADR-009)
        existing = db.scalar(
            select(Subject).where(func.lower(Subject.subject_code) == data.subjectCode.lower())
        )
        if existing:
            raise DomainException(
                code="DUPLICATE_SUBJECT_CODE",
                message=f"Subject code '{data.subjectCode}' already exists in catalog.",
                status_code=409,
            )

        # Verify department exists
        dept = db.get(Department, data.departmentId)
        if not dept or dept.status != EntityStatus.ACTIVE:
            raise DomainException(
                code="UNKNOWN_DEPARTMENT",
                message=f"Department with ID '{data.departmentId}' does not exist or is archived.",
                status_code=422,
            )

        new_subject = Subject(
            subject_code=data.subjectCode.upper(),
            subject_name=data.subjectName,
            department_id=data.departmentId,
            program_id=data.programId,
            semester=data.semester,
            credits=data.credits,
            default_duration_minutes=data.defaultDurationMinutes,
            priority=data.priority,
            preferred_dates=data.preferredDates,
            restricted_dates=data.restrictedDates,
            status=EntityStatus.ACTIVE,
        )
        db.add(new_subject)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.SUBJECT_CREATE,
            entity_type="subject",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=new_subject.id,
            after={
                "code": new_subject.subject_code,
                "name": new_subject.subject_name,
                "department_id": new_subject.department_id,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_subject)

        return SubjectResponse.model_validate(new_subject)

    @staticmethod
    def update_subject(
        db: Session,
        subject_id: str,
        data: SubjectUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> SubjectResponse:
        s = db.get(Subject, subject_id)
        if not s:
            raise DomainException(
                code="SUBJECT_NOT_FOUND", message="Subject not found.", status_code=404
            )

        check_department_scope(actor, s.department_id)

        before: dict[str, Any] = {
            "name": s.subject_name,
            "duration": s.default_duration_minutes,
            "status": enum_val(s.status),
        }

        if data.subjectName is not None:
            s.subject_name = data.subjectName
        if data.departmentId is not None:
            check_department_scope(actor, data.departmentId)
            s.department_id = data.departmentId
        if data.programId is not None:
            s.program_id = data.programId
        if data.semester is not None:
            s.semester = data.semester
        if data.credits is not None:
            s.credits = data.credits
        if data.defaultDurationMinutes is not None:
            s.default_duration_minutes = data.defaultDurationMinutes
        if data.priority is not None:
            s.priority = data.priority
        if data.preferredDates is not None:
            s.preferred_dates = data.preferredDates
        if data.restrictedDates is not None:
            s.restricted_dates = data.restrictedDates
        if data.status is not None:
            s.status = data.status

        audit_service.record(
            db=db,
            action=AuditAction.SUBJECT_UPDATE,
            entity_type="subject",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=s.id,
            before=before,
            after={
                "name": s.subject_name,
                "duration": s.default_duration_minutes,
                "status": enum_val(s.status),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(s)

        return SubjectService.get_subject_by_id(db, s.id, actor)

    @staticmethod
    def archive_subject(
        db: Session, subject_id: str, actor: User, request_id: str | None = None
    ) -> SubjectResponse:
        s = db.get(Subject, subject_id)
        if not s:
            raise DomainException(
                code="SUBJECT_NOT_FOUND", message="Subject not found.", status_code=404
            )

        check_department_scope(actor, s.department_id)

        # Soft archive instead of physical delete (Task P3.4)
        s.status = EntityStatus.ARCHIVED

        audit_service.record(
            db=db,
            action=AuditAction.SUBJECT_ARCHIVE,
            entity_type="subject",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=s.id,
            after={"status": EntityStatus.ARCHIVED.value},
            request_id=request_id,
        )
        db.commit()
        db.refresh(s)

        return SubjectResponse.model_validate(s)

    @staticmethod
    def get_subject_students(
        db: Session,
        subject_id: str,
        actor: User,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StudentResponse], int, int]:
        """Paginated list of students enrolled in this subject (staff only, Task P3.6)."""
        s = db.get(Subject, subject_id)
        if not s:
            raise DomainException(
                code="SUBJECT_NOT_FOUND", message="Subject not found.", status_code=404
            )

        check_department_scope(actor, s.department_id)

        query = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                Enrollment.subject_id == subject_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
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


subject_service = SubjectService()
