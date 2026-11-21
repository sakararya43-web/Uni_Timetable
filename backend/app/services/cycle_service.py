import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.error_handler import DomainException
from app.models.academic import AcademicYear, Semester, Subject
from app.models.enums import AuditAction, CycleStatus, EntityStatus, enum_val
from app.models.schedule import ExamAssignment
from app.models.scheduling import Exam, SchedulingCycle
from app.models.user import User
from app.schemas.cycle import (
    CycleConfiguration,
    CycleCreate,
    CycleUpdate,
    ExamResponse,
    ExamSyncResponse,
    ExamUpdate,
    SessionConfig,
)
from app.services.audit_service import audit_service
from app.services.staleness_service import staleness_service

# Legal Status Transitions (Task P5.1)
LEGAL_CYCLE_TRANSITIONS: dict[CycleStatus, set[CycleStatus]] = {
    CycleStatus.DRAFT: {CycleStatus.GENERATED, CycleStatus.ARCHIVED},
    CycleStatus.GENERATED: {CycleStatus.REVIEWED, CycleStatus.DRAFT, CycleStatus.ARCHIVED},
    CycleStatus.REVIEWED: {
        CycleStatus.PUBLISHED,
        CycleStatus.GENERATED,
        CycleStatus.DRAFT,
        CycleStatus.ARCHIVED,
    },
    CycleStatus.PUBLISHED: {CycleStatus.ARCHIVED},
    CycleStatus.ARCHIVED: set(),  # Terminal state
}


class CycleService:
    @staticmethod
    def validate_transition(current_status: CycleStatus, new_status: CycleStatus) -> None:
        """Enforces the strict status machine: Draft -> Generated -> Reviewed -> Published -> Archived (Task P5.1)."""
        curr_enum = (
            CycleStatus(current_status) if isinstance(current_status, str) else current_status
        )
        new_enum = CycleStatus(new_status) if isinstance(new_status, str) else new_status

        if curr_enum == new_enum:
            return

        allowed = LEGAL_CYCLE_TRANSITIONS.get(curr_enum, set())
        if new_enum not in allowed:
            allowed_names = [s.value for s in allowed] or ["None (Terminal)"]
            raise DomainException(
                code="INVALID_CYCLE_STATE_TRANSITION",
                message=(
                    f"Illegal state transition from '{curr_enum.value}' to '{new_enum.value}'. "
                    f"Allowed next states: {', '.join(allowed_names)}."
                ),
                status_code=422,
            )

    @staticmethod
    def get_cycles_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        academic_year_id: str | None = None,
        semester_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[SchedulingCycle], int, int]:
        query = select(SchedulingCycle)
        if academic_year_id:
            query = query.where(SchedulingCycle.academic_year_id == academic_year_id)
        if semester_id:
            query = query.where(SchedulingCycle.semester_id == semester_id)
        if status:
            query = query.where(SchedulingCycle.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(SchedulingCycle.name.ilike(pattern))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                query.order_by(SchedulingCycle.start_date.desc()).offset(offset).limit(page_size)
            ).all()
        )
        return items, total, total_pages

    @staticmethod
    def get_cycle_by_id(db: Session, cycle_id: str) -> SchedulingCycle:
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )
        return cycle

    @staticmethod
    def create_cycle(
        db: Session,
        data: CycleCreate,
        actor: User,
        request_id: str | None = None,
    ) -> SchedulingCycle:
        # Validate academic year exists
        ay = db.get(AcademicYear, data.academicYearId)
        if not ay or ay.status != EntityStatus.ACTIVE:
            raise DomainException(
                code="UNKNOWN_ACADEMIC_YEAR",
                message=f"Academic year '{data.academicYearId}' does not exist or is inactive.",
                status_code=422,
            )

        # Validate semester if specified
        if data.semesterId:
            sem = db.get(Semester, data.semesterId)
            if not sem or sem.academic_year_id != data.academicYearId:
                raise DomainException(
                    code="UNKNOWN_SEMESTER",
                    message="Semester not found or does not belong to specified academic year.",
                    status_code=422,
                )

        # Construct default configuration if not provided
        if data.configuration:
            config_dict = data.configuration.model_dump(mode="json", by_alias=True)
        else:
            default_config = CycleConfiguration(
                start_date=data.startDate,
                end_date=data.endDate,
                timezone=data.timezone,
                sessions=[
                    SessionConfig(
                        label="Morning", start_time="09:00", end_time="12:00", enabled=True
                    ),
                    SessionConfig(
                        label="Afternoon", start_time="14:00", end_time="17:00", enabled=True
                    ),
                ],
            )
            config_dict = default_config.model_dump(mode="json", by_alias=True)

        cycle = SchedulingCycle(
            name=data.name,
            academic_year_id=data.academicYearId,
            semester_id=data.semesterId,
            start_date=data.startDate,
            end_date=data.endDate,
            timezone=data.timezone,
            status=CycleStatus.DRAFT,
            configuration_json=config_dict,
            data_version=1,
            created_by=actor.id,
        )
        db.add(cycle)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_CREATE,
            entity_type="scheduling_cycle",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=cycle.id,
            after={
                "name": cycle.name,
                "start_date": str(cycle.start_date),
                "end_date": str(cycle.end_date),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(cycle)
        return cycle

    @staticmethod
    def update_cycle(
        db: Session,
        cycle_id: str,
        data: CycleUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> SchedulingCycle:
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )

        before: dict[str, Any] = {
            "name": cycle.name,
            "status": enum_val(cycle.status),
            "start_date": str(cycle.start_date),
            "end_date": str(cycle.end_date),
        }

        # 1. State machine check
        if data.status is not None:
            CycleService.validate_transition(cycle.status, data.status)
            cycle.status = data.status

        # 2. Config & Date edits after Generated mark cycle stale (Task P5.1)
        config_changed = False
        if data.name is not None:
            cycle.name = data.name
        if data.startDate is not None:
            cycle.start_date = data.startDate
            config_changed = True
        if data.endDate is not None:
            cycle.end_date = data.endDate
            config_changed = True
        if data.timezone is not None:
            cycle.timezone = data.timezone
            config_changed = True
        if data.configuration is not None:
            cycle.configuration_json = data.configuration.model_dump(mode="json", by_alias=True)
            config_changed = True

        if config_changed:
            staleness_service.bump_cycle_data_version(db, cycle_id)
            if cycle.status in (CycleStatus.GENERATED, CycleStatus.REVIEWED):
                cycle.status = CycleStatus.DRAFT

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_UPDATE,
            entity_type="scheduling_cycle",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=cycle.id,
            before=before,
            after={
                "name": cycle.name,
                "status": enum_val(cycle.status),
                "start_date": str(cycle.start_date),
                "end_date": str(cycle.end_date),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(cycle)
        return cycle

    @staticmethod
    def archive_cycle(
        db: Session, cycle_id: str, actor: User, request_id: str | None = None
    ) -> SchedulingCycle:
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )

        CycleService.validate_transition(cycle.status, CycleStatus.ARCHIVED)
        cycle.status = CycleStatus.ARCHIVED

        audit_service.record(
            db=db,
            action=AuditAction.CYCLE_ARCHIVE,
            entity_type="scheduling_cycle",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=cycle.id,
            after={"status": "Archived"},
            request_id=request_id,
        )
        db.commit()
        db.refresh(cycle)
        return cycle

    # ==========================================================================
    # Exam Synchronization & Overrides (Tasks P5.4, P5.5)
    # ==========================================================================
    @staticmethod
    def sync_exams(
        db: Session, cycle_id: str, actor: User, request_id: str | None = None
    ) -> ExamSyncResponse:
        """
        Synchronizes cycle's exams from active subjects matching scope (Task P5.4).
        Creates an Exam for each in-scope subject with default durations and priorities.
        """
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )

        # Read scope filters from configuration
        cfg = cycle.configuration_json or {}
        scope = cfg.get("scope", {})
        dept_ids = scope.get("departmentIds") or scope.get("department_ids")
        prog_ids = scope.get("programIds") or scope.get("program_ids")
        sem_nums = scope.get("semesterNumbers") or scope.get("semester_numbers")
        default_dur = cfg.get("defaultDurationMinutes", cfg.get("default_duration_minutes", 180))

        # Query in-scope active subjects
        sub_query = select(Subject).where(Subject.status == EntityStatus.ACTIVE)
        if dept_ids:
            sub_query = sub_query.where(Subject.department_id.in_(dept_ids))
        if prog_ids:
            sub_query = sub_query.where(Subject.program_id.in_(prog_ids))
        if sem_nums:
            sub_query = sub_query.where(Subject.semester.in_(sem_nums))

        in_scope_subjects = list(db.scalars(sub_query).all())
        in_scope_sub_ids = {s.id: s for s in in_scope_subjects}

        # Query existing exams in this cycle
        existing_exams = list(
            db.scalars(select(Exam).where(Exam.scheduling_cycle_id == cycle_id)).all()
        )
        existing_exam_map = {e.subject_id: e for e in existing_exams}

        added_count = 0
        removed_count = 0

        # Add missing exams
        for sub_id, subj in in_scope_sub_ids.items():
            if sub_id not in existing_exam_map:
                new_exam = Exam(
                    scheduling_cycle_id=cycle_id,
                    subject_id=sub_id,
                    duration_minutes=subj.default_duration_minutes or default_dur,
                    priority=subj.priority or 1,
                    preferred_dates=subj.preferred_dates or [],
                    restricted_dates=subj.restricted_dates or [],
                    status=EntityStatus.ACTIVE,
                )
                db.add(new_exam)
                added_count += 1

        # Remove out-of-scope exams only if no assignments exist (Task P5.4)
        for sub_id, exam in existing_exam_map.items():
            if sub_id not in in_scope_sub_ids:
                assignments_count = (
                    db.scalar(
                        select(func.count(ExamAssignment.id)).where(
                            ExamAssignment.exam_id == exam.id
                        )
                    )
                    or 0
                )
                if assignments_count == 0:
                    db.delete(exam)
                    removed_count += 1

        # Staleness signaling
        staleness_service.bump_cycle_data_version(db, cycle_id)
        db.commit()

        total_synced = (
            db.scalar(select(func.count(Exam.id)).where(Exam.scheduling_cycle_id == cycle_id)) or 0
        )

        return ExamSyncResponse(
            cycle_id=cycle_id,
            synced_exams_count=total_synced,
            added_count=added_count,
            removed_count=removed_count,
            message=f"Synced {total_synced} exams for cycle ({added_count} added, {removed_count} removed).",
        )

    @staticmethod
    def get_cycle_exams_paginated(
        db: Session,
        cycle_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExamResponse], int, int]:
        query = (
            select(Exam)
            .options(joinedload(Exam.subject))
            .where(Exam.scheduling_cycle_id == cycle_id)
        )
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        exams = list(
            db.scalars(query.order_by(Exam.created_at.asc()).offset(offset).limit(page_size)).all()
        )

        responses: list[ExamResponse] = []
        for e in exams:
            responses.append(
                ExamResponse(
                    id=e.id,
                    scheduling_cycle_id=e.scheduling_cycle_id,
                    subject_id=e.subject_id,
                    subject_code=e.subject.subject_code if e.subject else None,
                    subject_name=e.subject.subject_name if e.subject else None,
                    duration_minutes=e.duration_minutes,
                    priority=e.priority,
                    preferred_dates=e.preferred_dates or [],
                    restricted_dates=e.restricted_dates or [],
                    status=e.status,
                )
            )
        return responses, total, total_pages

    @staticmethod
    def update_exam_override(
        db: Session,
        exam_id: str,
        data: ExamUpdate,
        actor: User,
        request_id: str | None = None,
    ) -> ExamResponse:
        """Per-exam overrides: duration, preferred/restricted dates, priority (Task P5.5)."""
        exam = db.get(Exam, exam_id)
        if not exam:
            raise DomainException(
                code="EXAM_NOT_FOUND",
                message=f"Exam '{exam_id}' was not found.",
                status_code=404,
            )

        if data.durationMinutes is not None:
            exam.duration_minutes = data.durationMinutes
        if data.priority is not None:
            exam.priority = data.priority
        if data.preferredDates is not None:
            exam.preferred_dates = data.preferredDates
        if data.restrictedDates is not None:
            exam.restricted_dates = data.restrictedDates

        # Staleness signaling
        staleness_service.bump_cycle_data_version(db, exam.scheduling_cycle_id)
        db.commit()
        db.refresh(exam)

        subject = db.get(Subject, exam.subject_id)
        return ExamResponse(
            id=exam.id,
            scheduling_cycle_id=exam.scheduling_cycle_id,
            subject_id=exam.subject_id,
            subject_code=subject.subject_code if subject else None,
            subject_name=subject.subject_name if subject else None,
            duration_minutes=exam.duration_minutes,
            priority=exam.priority,
            preferred_dates=exam.preferred_dates or [],
            restricted_dates=exam.restricted_dates or [],
            status=exam.status,
        )


cycle_service = CycleService()
