import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import check_department_scope
from app.middleware.error_handler import DomainException
from app.models.academic import Student, Subject
from app.models.enums import AuditAction, EnrollmentStatus, EntityStatus
from app.models.scheduling import Enrollment, Exam, SchedulingCycle
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentValidationReport,
)
from app.services.audit_service import audit_service
from app.services.staleness_service import staleness_service


class EnrollmentService:
    @staticmethod
    def get_enrollments_paginated(
        db: Session,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        student_id: str | None = None,
        subject_id: str | None = None,
        cycle_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[EnrollmentResponse], int, int]:
        actor_role = actor.role.value if hasattr(actor.role, "value") else str(actor.role)
        query = select(Enrollment).options(
            joinedload(Enrollment.student), joinedload(Enrollment.subject)
        )

        if actor_role == "coordinator":
            query = query.join(Subject, Subject.id == Enrollment.subject_id).where(
                Subject.department_id == actor.department_id
            )

        if student_id:
            query = query.where(Enrollment.student_id == student_id)
        if subject_id:
            query = query.where(Enrollment.subject_id == subject_id)
        if cycle_id:
            query = query.where(Enrollment.cycle_id == cycle_id)
        if status:
            query = query.where(Enrollment.status == status)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        enrollments = list(
            db.scalars(
                query.order_by(Enrollment.created_at.desc()).offset(offset).limit(page_size)
            ).all()
        )

        items: list[EnrollmentResponse] = []
        for enr in enrollments:
            items.append(
                EnrollmentResponse(
                    id=enr.id,
                    student_id=enr.student_id,
                    student_number=enr.student.student_number if enr.student else None,
                    student_name=enr.student.full_name if enr.student else None,
                    subject_id=enr.subject_id,
                    subject_code=enr.subject.subject_code if enr.subject else None,
                    subject_name=enr.subject.subject_name if enr.subject else None,
                    cycle_id=enr.cycle_id,
                    status=enr.status,
                )
            )

        return items, total, total_pages

    @staticmethod
    def create_enrollment(
        db: Session,
        data: EnrollmentCreate,
        actor: User,
        request_id: str | None = None,
    ) -> EnrollmentResponse:
        # Validate student existence and active status
        student = db.get(Student, data.studentId)
        if not student:
            raise DomainException(
                code="UNKNOWN_STUDENT",
                message=f"Student with ID '{data.studentId}' was not found.",
                status_code=404,
            )
        if student.status != EntityStatus.ACTIVE:
            raise DomainException(
                code="STUDENT_ARCHIVED",
                message=f"Cannot enroll student '{student.student_number}' because the student record is archived.",
                status_code=422,
            )

        # Validate subject existence and active status
        subject = db.get(Subject, data.subjectId)
        if not subject:
            raise DomainException(
                code="UNKNOWN_SUBJECT",
                message=f"Subject with ID '{data.subjectId}' was not found.",
                status_code=404,
            )
        if subject.status != EntityStatus.ACTIVE:
            raise DomainException(
                code="SUBJECT_ARCHIVED",
                message=f"Cannot enroll into subject '{subject.subject_code}' because it is archived.",
                status_code=422,
            )

        # Validate scheduling cycle existence
        cycle = db.get(SchedulingCycle, data.cycleId)
        if not cycle:
            raise DomainException(
                code="UNKNOWN_CYCLE",
                message=f"Scheduling cycle with ID '{data.cycleId}' was not found.",
                status_code=404,
            )

        # Department scoping for coordinator
        check_department_scope(actor, subject.department_id)

        # Check existing enrollment
        existing = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == data.studentId,
                Enrollment.subject_id == data.subjectId,
                Enrollment.cycle_id == data.cycleId,
            )
        )

        if existing:
            if existing.status == EnrollmentStatus.ACTIVE:
                raise DomainException(
                    code="DUPLICATE_ENROLLMENT",
                    message=(
                        f"Student '{student.student_number}' is already actively enrolled in "
                        f"subject '{subject.subject_code}' for cycle '{cycle.name}'."
                    ),
                    status_code=409,
                )
            else:
                # Re-activate previously withdrawn enrollment
                before_state = {"status": existing.status.value if hasattr(existing.status, "value") else str(existing.status)}
                existing.status = EnrollmentStatus.ACTIVE

                # Staleness signaling (Task P3.16)
                staleness_service.bump_cycle_data_version(db, data.cycleId)

                audit_service.record(
                    db=db,
                    action=AuditAction.ENROLLMENT_CREATE,
                    entity_type="enrollment",
                    actor_email=actor.email,
                    actor_id=actor.id,
                    entity_id=existing.id,
                    before=before_state,
                    after={
                        "student_id": existing.student_id,
                        "subject_id": existing.subject_id,
                        "cycle_id": existing.cycle_id,
                        "status": "active",
                    },
                    request_id=request_id,
                )
                db.commit()
                db.refresh(existing)

                return EnrollmentResponse(
                    id=existing.id,
                    student_id=existing.student_id,
                    student_number=student.student_number,
                    student_name=student.full_name,
                    subject_id=existing.subject_id,
                    subject_code=subject.subject_code,
                    subject_name=subject.subject_name,
                    cycle_id=existing.cycle_id,
                    status=existing.status,
                )

        # Create new active enrollment
        new_enr = Enrollment(
            student_id=data.studentId,
            subject_id=data.subjectId,
            cycle_id=data.cycleId,
            status=EnrollmentStatus.ACTIVE,
        )
        db.add(new_enr)
        db.flush()

        # Staleness signaling (Task P3.16)
        staleness_service.bump_cycle_data_version(db, data.cycleId)

        audit_service.record(
            db=db,
            action=AuditAction.ENROLLMENT_CREATE,
            entity_type="enrollment",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=new_enr.id,
            after={
                "student_id": new_enr.student_id,
                "subject_id": new_enr.subject_id,
                "cycle_id": new_enr.cycle_id,
                "status": "active",
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_enr)

        return EnrollmentResponse(
            id=new_enr.id,
            student_id=new_enr.student_id,
            student_number=student.student_number,
            student_name=student.full_name,
            subject_id=new_enr.subject_id,
            subject_code=subject.subject_code,
            subject_name=subject.subject_name,
            cycle_id=new_enr.cycle_id,
            status=new_enr.status,
        )

    @staticmethod
    def withdraw_enrollment(
        db: Session,
        enrollment_id: str,
        actor: User,
        request_id: str | None = None,
    ) -> EnrollmentResponse:
        enr = db.get(Enrollment, enrollment_id)
        if not enr:
            raise DomainException(
                code="ENROLLMENT_NOT_FOUND",
                message="Enrollment record not found.",
                status_code=404,
            )

        subject = db.get(Subject, enr.subject_id)
        if subject:
            check_department_scope(actor, subject.department_id)

        before_status = enr.status.value if hasattr(enr.status, "value") else str(enr.status)
        enr.status = EnrollmentStatus.WITHDRAWN

        # Staleness signaling (Task P3.16)
        staleness_service.bump_cycle_data_version(db, enr.cycle_id)

        audit_service.record(
            db=db,
            action=AuditAction.ENROLLMENT_WITHDRAW,
            entity_type="enrollment",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=enr.id,
            before={"status": before_status},
            after={"status": "withdrawn"},
            request_id=request_id,
        )
        db.commit()
        db.refresh(enr)

        student = db.get(Student, enr.student_id)
        return EnrollmentResponse(
            id=enr.id,
            student_id=enr.student_id,
            student_number=student.student_number if student else None,
            student_name=student.full_name if student else None,
            subject_id=enr.subject_id,
            subject_code=subject.subject_code if subject else None,
            subject_name=subject.subject_name if subject else None,
            cycle_id=enr.cycle_id,
            status=enr.status,
        )

    @staticmethod
    def validate_enrollments_integrity(
        db: Session,
        actor: User,
        cycle_id: str | None = None,
    ) -> EnrollmentValidationReport:
        """
        Integrity diagnostic reporting (Task P3.15):
        Reports duplicates, orphan references, students with zero enrollments,
        subjects with zero enrollments, and cycles with zero exams.
        """
        # 1. Duplicates: Active student-subject-cycle pairs with count > 1
        dup_query = (
            select(
                Enrollment.student_id,
                Enrollment.subject_id,
                Enrollment.cycle_id,
                func.count(Enrollment.id).label("cnt"),
            )
            .where(Enrollment.status == EnrollmentStatus.ACTIVE)
            .group_by(Enrollment.student_id, Enrollment.subject_id, Enrollment.cycle_id)
            .having(func.count(Enrollment.id) > 1)
        )
        if cycle_id:
            dup_query = dup_query.where(Enrollment.cycle_id == cycle_id)
        dup_records = list(db.execute(dup_query).all())
        dup_count = len(dup_records)

        # 2. Orphan references: enrollments pointing to nonexistent student, subject, or cycle
        orphan_student_count = db.scalar(
            select(func.count(Enrollment.id)).where(
                ~Enrollment.student_id.in_(select(Student.id))
            )
        ) or 0
        orphan_subject_count = db.scalar(
            select(func.count(Enrollment.id)).where(
                ~Enrollment.subject_id.in_(select(Subject.id))
            )
        ) or 0
        orphan_cycle_count = db.scalar(
            select(func.count(Enrollment.id)).where(
                ~Enrollment.cycle_id.in_(select(SchedulingCycle.id))
            )
        ) or 0
        orphan_count = orphan_student_count + orphan_subject_count + orphan_cycle_count

        # 3. Active students with zero active enrollments
        st_enr_subquery = select(Enrollment.student_id).where(
            Enrollment.status == EnrollmentStatus.ACTIVE
        )
        if cycle_id:
            st_enr_subquery = st_enr_subquery.where(Enrollment.cycle_id == cycle_id)

        zero_enr_students = db.scalar(
            select(func.count(Student.id)).where(
                Student.status == EntityStatus.ACTIVE,
                ~Student.id.in_(st_enr_subquery),
            )
        ) or 0

        # 4. Active subjects with zero active enrollments
        sub_enr_subquery = select(Enrollment.subject_id).where(
            Enrollment.status == EnrollmentStatus.ACTIVE
        )
        if cycle_id:
            sub_enr_subquery = sub_enr_subquery.where(Enrollment.cycle_id == cycle_id)

        zero_enr_subjects = db.scalar(
            select(func.count(Subject.id)).where(
                Subject.status == EntityStatus.ACTIVE,
                ~Subject.id.in_(sub_enr_subquery),
            )
        ) or 0

        # 5. Cycles with zero configured exams
        exam_cycle_subquery = select(Exam.scheduling_cycle_id)
        zero_exam_cycles_query = select(func.count(SchedulingCycle.id)).where(
            ~SchedulingCycle.id.in_(exam_cycle_subquery)
        )
        if cycle_id:
            zero_exam_cycles_query = zero_exam_cycles_query.where(SchedulingCycle.id == cycle_id)
        zero_exam_cycles = db.scalar(zero_exam_cycles_query) or 0

        is_valid = (dup_count == 0) and (orphan_count == 0) and (zero_exam_cycles == 0)

        details: dict[str, Any] = {
            "duplicate_records": [
                {"student_id": r[0], "subject_id": r[1], "cycle_id": r[2], "count": r[3]}
                for r in dup_records
            ],
            "orphan_breakdown": {
                "orphan_students": orphan_student_count,
                "orphan_subjects": orphan_subject_count,
                "orphan_cycles": orphan_cycle_count,
            },
            "cycle_id_filter": cycle_id,
        }

        return EnrollmentValidationReport(
            is_valid=is_valid,
            duplicate_records_count=dup_count,
            orphan_references_count=orphan_count,
            students_with_zero_enrollments_count=zero_enr_students,
            subjects_with_zero_enrollments_count=zero_enr_subjects,
            cycles_with_zero_exams_count=zero_exam_cycles,
            details=details,
        )


enrollment_service = EnrollmentService()
