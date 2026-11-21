"""Schedule Version Service: Lifecycle, Manual Editing, Locking, Regeneration, and Diff.

PRD §15, §17.14, §17.15, §18.7, Tasks P9.1 - P9.21.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.algorithms.dsatur import dsatur
from app.algorithms.greedy import greedy_color
from app.algorithms.slot_mapper import ExamInfo, SlotInfo, map_colors_to_slots
from app.algorithms.welsh_powell import welsh_powell
from app.middleware.error_handler import DomainException
from app.models.enums import (
    AuditAction,
    EnrollmentStatus,
    ScheduleStatus,
    enum_val,
)
from app.models.schedule import ExamAssignment, ScheduleVersion
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot
from app.models.user import User
from app.schemas.schedule import (
    HardViolationSchema,
)
from app.schemas.schedule_version import (
    BulkLockRequest,
    ChangeImpactReportResponse,
    ConflictingExamItem,
    LockValidationResponse,
    MovedExamItem,
    PreviewMoveResponse,
    ScheduleRegenerateRequest,
    SwapAssignmentsRequest,
    UpdateAssignmentRequest,
)
from app.services.audit_service import audit_service
from app.services.graph_service import graph_service
from app.services.schedule_validator import validate_schedule
from app.services.soft_constraint_service import evaluate_soft_constraints


class ScheduleVersionService:
    """Orchestrates schedule version lifecycle, incremental manual editing, locks, and regeneration."""

    @staticmethod
    def _ensure_version_editable(version: ScheduleVersion) -> None:
        """Enforces FR-19 / Task P9.2: Candidate and Reviewed are editable; Published and Archived are immutable."""
        val = enum_val(version.status)
        if val in [enum_val(ScheduleStatus.PUBLISHED), enum_val(ScheduleStatus.ARCHIVED)]:
            raise DomainException(
                code="SCHEDULE_IMMUTABLE",
                message=(
                    f"Schedule version {version.version_number} is {val} and cannot be modified. "
                    "Clone to a new Candidate version first (POST /schedules/{id}/clone)."
                ),
                status_code=409,
            )

    @staticmethod
    def _check_concurrency(version: ScheduleVersion, expected_row_version: int | None) -> None:
        """Enforces optimistic concurrency locking (Task P9.10)."""
        if expected_row_version is not None and expected_row_version != version.row_version:
            raise DomainException(
                code="CONCURRENT_MODIFICATION",
                message=(
                    f"Schedule version has been modified by another session "
                    f"(expected row_version {expected_row_version}, current {version.row_version}). "
                    "Please refresh and retry."
                ),
                status_code=409,
            )

    @staticmethod
    def list_cycle_schedules(db: Session, cycle_id: str) -> list[ScheduleVersion]:
        """Lists all schedule versions for a scheduling cycle (Task P9.1)."""
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(code="CYCLE_NOT_FOUND", message="Cycle not found.", status_code=404)

        stmt = (
            select(ScheduleVersion)
            .where(ScheduleVersion.scheduling_cycle_id == cycle_id)
            .options(joinedload(ScheduleVersion.assignments))
            .order_by(ScheduleVersion.version_number.desc())
        )
        return list(db.scalars(stmt).unique().all())

    @staticmethod
    def get_version(db: Session, version_id: str) -> ScheduleVersion:
        """Fetches a single schedule version with assignments and related entities (Task P9.1)."""
        stmt = (
            select(ScheduleVersion)
            .where(ScheduleVersion.id == version_id)
            .options(
                joinedload(ScheduleVersion.assignments).joinedload(ExamAssignment.exam).joinedload(Exam.subject),
                joinedload(ScheduleVersion.assignments).joinedload(ExamAssignment.time_slot),
            )
        )
        ver = db.scalar(stmt)
        if not ver:
            raise DomainException(code="SCHEDULE_VERSION_NOT_FOUND", message="Schedule version not found.", status_code=404)
        return ver

    @staticmethod
    def clone_version(
        db: Session,
        version_id: str,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Clones an existing schedule version (even Published) into a new editable Candidate version (P9.2)."""
        source = ScheduleVersionService.get_version(db, version_id)

        # Determine next version number in the cycle
        max_ver = db.scalar(
            select(func.max(ScheduleVersion.version_number))
            .where(ScheduleVersion.scheduling_cycle_id == source.scheduling_cycle_id)
        ) or 0
        new_version_num = max_ver + 1

        new_version = ScheduleVersion(
            scheduling_cycle_id=source.scheduling_cycle_id,
            version_number=new_version_num,
            schedule_run_id=source.schedule_run_id,
            status=ScheduleStatus.CANDIDATE,
            validation_report_json=source.validation_report_json,
            soft_score=source.soft_score,
            row_version=1,
            created_by=actor.id,
        )
        db.add(new_version)
        db.flush()

        for a in source.assignments:
            cloned_assignment = ExamAssignment(
                schedule_version_id=new_version.id,
                exam_id=a.exam_id,
                time_slot_id=a.time_slot_id,
                color_id=a.color_id,
                locked=a.locked,
                manual_override=a.manual_override,
            )
            db.add(cloned_assignment)

        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_CLONE,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=new_version.id,
            after={
                "sourceVersionId": source.id,
                "sourceVersionNumber": source.version_number,
                "newVersionNumber": new_version_num,
                "cycleId": source.scheduling_cycle_id,
                "assignmentCount": len(source.assignments),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_version)
        return ScheduleVersionService.get_version(db, new_version.id)

    @staticmethod
    def archive_version(
        db: Session,
        version_id: str,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Archives a schedule version (Task P9.4)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        if enum_val(ver.status) == enum_val(ScheduleStatus.ARCHIVED):
            return ver

        old_status = enum_val(ver.status)
        ver.status = ScheduleStatus.ARCHIVED
        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_ARCHIVE,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=ver.id,
            after={
                "versionNumber": ver.version_number,
                "oldStatus": old_status,
                "newStatus": ScheduleStatus.ARCHIVED.value,
                "cycleId": ver.scheduling_cycle_id,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(ver)
        return ver

    @staticmethod
    def preview_assignment_move(
        db: Session,
        version_id: str,
        assignment_id: str,
        target_slot_id: str,
    ) -> PreviewMoveResponse:
        """Dry-run move preview verifying all hard constraints and calculating soft penalty delta (P9.5, P9.7)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        assignment = next((a for a in ver.assignments if a.id == assignment_id), None)
        if not assignment:
            raise DomainException(code="ASSIGNMENT_NOT_FOUND", message="Assignment not found.", status_code=404)

        target_slot = db.get(TimeSlot, target_slot_id)
        if not target_slot or target_slot.scheduling_cycle_id != ver.scheduling_cycle_id:
            raise DomainException(code="SLOT_NOT_FOUND", message="Target slot not found in this cycle.", status_code=404)

        cycle_id = ver.scheduling_cycle_id

        # Load all exams and slots for cycle
        exams_list = list(
            db.scalars(
                select(Exam)
                .where(Exam.scheduling_cycle_id == cycle_id)
                .options(joinedload(Exam.subject))
            ).all()
        )
        slots_list = list(
            db.scalars(
                select(TimeSlot)
                .where(TimeSlot.scheduling_cycle_id == cycle_id)
            ).all()
        )

        exams_dict = {
            e.id: {
                "id": e.id,
                "subject_code": e.subject.subject_code,
                "duration_minutes": e.duration_minutes,
                "restricted_dates": e.restricted_dates or [],
                "preferred_dates": e.preferred_dates or [],
                "cycle_id": e.scheduling_cycle_id,
                "locked_slot_id": e.id if False else None,
            }
            for e in exams_list
        }

        slots_dict = {
            s.id: {
                "id": s.id,
                "date": s.date,
                "start_time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, "strftime") else str(s.start_time),
                "end_time": s.end_time.strftime("%H:%M") if hasattr(s.end_time, "strftime") else str(s.end_time),
                "duration_minutes": s.duration_minutes,
                "is_enabled": s.enabled,
                "slot_index": s.slot_index,
                "session_label": s.session_label,
                "cycle_id": s.scheduling_cycle_id,
            }
            for s in slots_list
        }

        # Simulated assignments
        simulated_assignments: list[dict[str, Any]] = []
        for a in ver.assignments:
            slot_id = target_slot_id if a.id == assignment_id else a.time_slot_id
            simulated_assignments.append({
                "exam_id": a.exam_id,
                "time_slot_id": slot_id,
                "color_id": a.color_id,
                "locked": a.locked,
            })

        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle_id,
                )
            ).all()
        )
        enrollments_tuples: list[tuple[str, str]] = [(str(r[0]), str(r[1])) for r in enrollments]

        validation_report = validate_schedule(
            exams=exams_dict,
            slots=slots_dict,
            assignments=simulated_assignments,
            enrollments=enrollments_tuples,
            cycle_id=cycle_id,
        )

        cycle = db.get(SchedulingCycle, cycle_id)
        weights = (cycle.configuration_json or {}).get("softConstraintWeights", {}) if cycle else {}
        new_soft_score, _ = evaluate_soft_constraints(
            assignments=simulated_assignments,
            slots=slots_dict,
            exams=exams_dict,
            enrollments=enrollments_tuples,
            weights=weights,
        )

        # Identify conflicting exams already scheduled in target_slot
        conflicting_exams: list[ConflictingExamItem] = []
        target_exam_ids = [
            a.exam_id
            for a in ver.assignments
            if a.time_slot_id == target_slot_id and a.id != assignment_id
        ]

        if target_exam_ids:
            moving_students = {
                r[0] for r in enrollments_tuples if r[1] == assignment.exam_id
            }
            for target_eid in target_exam_ids:
                other_students = {
                    r[0] for r in enrollments_tuples if r[1] == target_eid
                }
                shared = moving_students.intersection(other_students)
                if shared:
                    other_exam = next((e for e in exams_list if e.id == target_eid), None)
                    conflicting_exams.append(
                        ConflictingExamItem(
                            exam_id=target_eid,
                            subject_code=other_exam.subject.subject_code if other_exam else target_eid,
                            subject_name=other_exam.subject.subject_name if other_exam else target_eid,
                            shared_student_count=len(shared),
                        )
                    )

        soft_delta = round(new_soft_score - ver.soft_score, 4)

        return PreviewMoveResponse(
            valid=validation_report.valid and not assignment.locked,
            violations=[
                HardViolationSchema(
                    type=v.type,
                    exam_ids=v.exam_ids,
                    slot_id=v.slot_id,
                    message=v.message,
                    shared_student_count=v.shared_student_count,
                )
                for v in validation_report.hard_violations
            ],
            conflicting_exams=conflicting_exams,
            soft_penalty_delta=soft_delta,
            new_soft_score=new_soft_score,
            exam_locked=assignment.locked,
        )

    @staticmethod
    def move_assignment(
        db: Session,
        version_id: str,
        assignment_id: str,
        req: UpdateAssignmentRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Moves an exam assignment to a target slot with strict verification and optimistic concurrency (P9.6 - P9.11)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        ScheduleVersionService._ensure_version_editable(ver)
        ScheduleVersionService._check_concurrency(ver, req.expectedRowVersion)

        assignment = next((a for a in ver.assignments if a.id == assignment_id), None)
        if not assignment:
            raise DomainException(code="ASSIGNMENT_NOT_FOUND", message="Assignment not found.", status_code=404)

        if assignment.locked:
            raise DomainException(
                code="EXAM_LOCKED",
                message=(
                    f"Exam {assignment.exam.subject.subject_code} is locked to its slot "
                    "and cannot be moved unless unlocked first (POST /schedules/{id}/assignments/{aid}/unlock)."
                ),
                status_code=409,
            )

        preview = ScheduleVersionService.preview_assignment_move(
            db=db,
            version_id=version_id,
            assignment_id=assignment_id,
            target_slot_id=req.timeSlotId,
        )

        if not preview.valid:
            violation_msg = preview.violations[0].message if preview.violations else "Hard constraint violation."
            raise DomainException(
                code="INVALID_MOVE",
                message=f"Cannot move exam: {violation_msg}",
                status_code=422,
            )

        old_slot_id = assignment.time_slot_id
        assignment.time_slot_id = req.timeSlotId
        assignment.manual_override = True

        ver.row_version += 1
        ver.soft_score = preview.newSoftScore
        ver.validation_report_json = {
            "valid": True,
            "hardViolations": [v.model_dump(by_alias=True) for v in preview.violations],
            "softPenaltyTotal": preview.newSoftScore,
            "warnings": [],
        }
        if enum_val(ver.status) == enum_val(ScheduleStatus.REVIEWED):
            ver.status = ScheduleStatus.CANDIDATE

        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_EDIT,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="exam_assignment",
            entity_id=assignment.id,
            before={"timeSlotId": old_slot_id},
            after={
                "versionId": ver.id,
                "examId": assignment.exam_id,
                "subjectCode": assignment.exam.subject.subject_code,
                "fromSlotId": old_slot_id,
                "toSlotId": req.timeSlotId,
                "manualOverride": True,
                "newRowVersion": ver.row_version,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(ver)
        return ScheduleVersionService.get_version(db, ver.id)

    @staticmethod
    def swap_assignments(
        db: Session,
        version_id: str,
        req: SwapAssignmentsRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Atomically swaps the time slots of two examinations with hard constraint verification (P9.9)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        ScheduleVersionService._ensure_version_editable(ver)
        ScheduleVersionService._check_concurrency(ver, req.expectedRowVersion)

        assign_a = next((a for a in ver.assignments if a.id == req.assignmentIdA), None)
        assign_b = next((a for a in ver.assignments if a.id == req.assignmentIdB), None)

        if not assign_a or not assign_b:
            raise DomainException(code="ASSIGNMENT_NOT_FOUND", message="One or both assignments not found.", status_code=404)

        if assign_a.locked or assign_b.locked:
            locked_name = assign_a.exam.subject.subject_code if assign_a.locked else assign_b.exam.subject.subject_code
            raise DomainException(
                code="EXAM_LOCKED",
                message=f"Cannot swap locked exam {locked_name}. Unlock first.",
                status_code=409,
            )

        cycle_id = ver.scheduling_cycle_id
        target_slot_a = assign_b.time_slot_id
        target_slot_b = assign_a.time_slot_id

        # Simulate swap
        simulated_assignments: list[dict[str, Any]] = []
        for a in ver.assignments:
            sid = a.time_slot_id
            if a.id == assign_a.id:
                sid = target_slot_a
            elif a.id == assign_b.id:
                sid = target_slot_b
            simulated_assignments.append({
                "exam_id": a.exam_id,
                "time_slot_id": sid,
                "color_id": a.color_id,
                "locked": a.locked,
            })

        exams_list = list(
            db.scalars(select(Exam).where(Exam.scheduling_cycle_id == cycle_id).options(joinedload(Exam.subject))).all()
        )
        slots_list = list(db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle_id)).all())

        exams_dict = {
            e.id: {
                "id": e.id,
                "subject_code": e.subject.subject_code,
                "duration_minutes": e.duration_minutes,
                "restricted_dates": e.restricted_dates or [],
                "preferred_dates": e.preferred_dates or [],
                "cycle_id": e.scheduling_cycle_id,
                "locked_slot_id": None,
            }
            for e in exams_list
        }
        slots_dict = {
            s.id: {
                "id": s.id,
                "date": s.date,
                "start_time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, "strftime") else str(s.start_time),
                "end_time": s.end_time.strftime("%H:%M") if hasattr(s.end_time, "strftime") else str(s.end_time),
                "duration_minutes": s.duration_minutes,
                "is_enabled": s.enabled,
                "slot_index": s.slot_index,
                "session_label": s.session_label,
                "cycle_id": s.scheduling_cycle_id,
            }
            for s in slots_list
        }

        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle_id,
                )
            ).all()
        )
        enrollments_tuples: list[tuple[str, str]] = [(str(r[0]), str(r[1])) for r in enrollments]

        report = validate_schedule(
            exams=exams_dict,
            slots=slots_dict,
            assignments=simulated_assignments,
            enrollments=enrollments_tuples,
            cycle_id=cycle_id,
        )

        if not report.valid:
            msg = report.hard_violations[0].message if report.hard_violations else "Hard constraint violation on swap."
            raise DomainException(code="INVALID_SWAP", message=f"Cannot swap exams: {msg}", status_code=422)

        cycle = db.get(SchedulingCycle, cycle_id)
        weights = (cycle.configuration_json or {}).get("softConstraintWeights", {}) if cycle else {}
        new_soft_score, soft_breakdown = evaluate_soft_constraints(
            assignments=simulated_assignments,
            slots=slots_dict,
            exams=exams_dict,
            enrollments=enrollments_tuples,
            weights=weights,
        )

        # Apply swap
        assign_a.time_slot_id = target_slot_a
        assign_a.manual_override = True
        assign_b.time_slot_id = target_slot_b
        assign_b.manual_override = True

        ver.row_version += 1
        ver.soft_score = new_soft_score
        ver.validation_report_json = {
            "valid": True,
            "hardViolations": [],
            "softPenaltyTotal": new_soft_score,
            "softBreakdown": [
                {
                    "rule": getattr(sb, "rule", sb.get("rule") if isinstance(sb, dict) else ""),
                    "weight": getattr(sb, "weight", sb.get("weight") if isinstance(sb, dict) else 0.0),
                    "count": getattr(sb, "count", sb.get("count") if isinstance(sb, dict) else 0),
                    "penalty": getattr(sb, "penalty", sb.get("penalty") if isinstance(sb, dict) else 0.0),
                    "message": getattr(sb, "message", sb.get("message") if isinstance(sb, dict) else ""),
                }
                for sb in soft_breakdown
            ],
            "warnings": [],
        }
        if enum_val(ver.status) == enum_val(ScheduleStatus.REVIEWED):
            ver.status = ScheduleStatus.CANDIDATE

        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_EDIT,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=ver.id,
            after={
                "operation": "swap",
                "assignmentA": assign_a.id,
                "assignmentB": assign_b.id,
                "examA": assign_a.exam_id,
                "examB": assign_b.exam_id,
                "newRowVersion": ver.row_version,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(ver)
        return ScheduleVersionService.get_version(db, ver.id)

    @staticmethod
    def set_assignment_lock(
        db: Session,
        version_id: str,
        assignment_id: str,
        locked: bool,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Locks or unlocks an individual assignment (Task P9.12)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        ScheduleVersionService._ensure_version_editable(ver)

        assignment = next((a for a in ver.assignments if a.id == assignment_id), None)
        if not assignment:
            raise DomainException(code="ASSIGNMENT_NOT_FOUND", message="Assignment not found.", status_code=404)

        if assignment.locked == locked:
            return ver

        assignment.locked = locked
        ver.row_version += 1

        action = AuditAction.EXAM_LOCK if locked else AuditAction.EXAM_UNLOCK
        audit_service.record(
            db=db,
            action=action,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="exam_assignment",
            entity_id=assignment.id,
            after={
                "versionId": ver.id,
                "examId": assignment.exam_id,
                "subjectCode": assignment.exam.subject.subject_code,
                "timeSlotId": assignment.time_slot_id,
                "locked": locked,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(ver)
        return ScheduleVersionService.get_version(db, ver.id)

    @staticmethod
    def bulk_lock_assignments(
        db: Session,
        version_id: str,
        req: BulkLockRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Bulk locks or unlocks assignments by date, session label, or explicit exam list (Task P9.14)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        ScheduleVersionService._ensure_version_editable(ver)

        lock_target = (req.action.lower() == "lock")
        affected_count = 0

        for a in ver.assignments:
            match = True
            if req.examIds is not None and a.exam_id not in req.examIds:
                match = False
            if req.date is not None and str(a.time_slot.date) != str(req.date):
                match = False
            if req.sessionLabel is not None and a.time_slot.session_label != req.sessionLabel:
                match = False

            if match and a.locked != lock_target:
                a.locked = lock_target
                affected_count += 1

        if affected_count > 0:
            ver.row_version += 1
            action = AuditAction.EXAM_LOCK if lock_target else AuditAction.EXAM_UNLOCK
            audit_service.record(
                db=db,
                action=action,
                actor_email=actor.email,
                actor_id=actor.id,
                entity_type="schedule_version",
                entity_id=ver.id,
                after={
                    "operation": "bulk_lock",
                    "action": req.action,
                    "affectedCount": affected_count,
                    "date": req.date,
                    "sessionLabel": req.sessionLabel,
                },
                request_id=request_id,
            )
            db.commit()
            db.refresh(ver)

        return ScheduleVersionService.get_version(db, ver.id)

    @staticmethod
    def validate_locks(db: Session, version_id: str) -> LockValidationResponse:
        """Validates that all currently locked exams in the version are mutually compatible (P9.15)."""
        ver = ScheduleVersionService.get_version(db, version_id)
        locked_assignments = [a for a in ver.assignments if a.locked]

        conflicts: list[str] = []
        cycle_id = ver.scheduling_cycle_id

        # Group locked exams by slot
        by_slot: dict[str, list[ExamAssignment]] = {}
        for a in locked_assignments:
            by_slot.setdefault(a.time_slot_id, []).append(a)

        # Check shared students in the same slot
        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle_id,
                )
            ).all()
        )
        exam_students: dict[str, set[str]] = {}
        for sid, eid in enrollments:
            exam_students.setdefault(str(eid), set()).add(str(sid))

        for slot_id, slot_assigns in by_slot.items():
            if len(slot_assigns) > 1:
                for i in range(len(slot_assigns)):
                    for j in range(i + 1, len(slot_assigns)):
                        ea = slot_assigns[i]
                        eb = slot_assigns[j]
                        shared = exam_students.get(ea.exam_id, set()).intersection(
                            exam_students.get(eb.exam_id, set())
                        )
                        if shared:
                            conflicts.append(
                                f"Locked conflict: Exam {ea.exam.subject.subject_code} and "
                                f"{eb.exam.subject.subject_code} are both locked to slot {slot_id} "
                                f"but share {len(shared)} student(s)."
                            )

        return LockValidationResponse(
            valid=(len(conflicts) == 0),
            conflicts=conflicts,
            locked_count=len(locked_assignments),
        )

    @staticmethod
    def regenerate_schedule(
        db: Session,
        version_id: str,
        req: ScheduleRegenerateRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Regenerates schedule with locked exam preservation and disruption minimization (P9.16 - P9.20)."""
        source_ver = ScheduleVersionService.get_version(db, version_id)
        cycle_id = source_ver.scheduling_cycle_id

        # 1. Validate lock set compatibility
        lock_val = ScheduleVersionService.validate_locks(db, version_id)
        if not lock_val.valid:
            raise DomainException(
                code="LOCKED_CONFLICT",
                message=f"Cannot regenerate: {lock_val.conflicts[0]}",
                status_code=409,
            )

        # 2. Check for enrollment data staleness (P9.20)
        is_stale = graph_service.is_cycle_graph_stale(db, cycle_id)
        if is_stale:
            if req.autoRebuildGraph:
                graph_service.build_graph_snapshot(
                    db=db, cycle_id=cycle_id, actor=actor, force=True, request_id=request_id
                )
            else:
                raise DomainException(
                    code="GRAPH_STALE",
                    message="Academic or enrollment data has changed since last generation. Set autoRebuildGraph=true to confirm.",
                    status_code=409,
                )

        latest_snapshot = graph_service.get_latest_snapshot(db, cycle_id)
        if not latest_snapshot:
            latest_snapshot, _, _ = graph_service.build_graph_snapshot(
                db=db, cycle_id=cycle_id, actor=actor, force=False, request_id=request_id
            )

        # 3. Load locked assignments
        locked_exam_map: dict[str, str] = {}
        if req.preserveLockedExams:
            locked_exam_map = {
                a.exam_id: a.time_slot_id
                for a in source_ver.assignments
                if a.locked
            }

        # 4. Group locked exams by slot to assign reserved color classes (P8.4)
        distinct_locked_slots = sorted(set(locked_exam_map.values()))
        slot_to_reserved_color = {sid: idx for idx, sid in enumerate(distinct_locked_slots)}
        precolored: dict[str, int] = {
            eid: slot_to_reserved_color[sid]
            for eid, sid in locked_exam_map.items()
        }

        # 5. Execute coloring algorithm
        adjacency_data = (latest_snapshot.graph_data_json or {}).get("adjacency", {})
        adj: dict[str, set[str]] = {v: set(nbrs) for v, nbrs in adjacency_data.items()}
        algo = req.algorithm.lower()
        if algo == "greedy":
            coloring_result = greedy_color(adj, precolored=precolored)
        elif algo == "welsh_powell":
            coloring_result = welsh_powell(adj, precolored=precolored)
        elif algo == "dsatur":
            coloring_result = dsatur(adj, precolored=precolored)
        else:
            raise DomainException(code="INVALID_ALGORITHM", message=f"Unknown algorithm '{algo}'.", status_code=400)

        # 6. Map color classes to slots with disruption minimization (P9.17)
        exams_list = list(
            db.scalars(select(Exam).where(Exam.scheduling_cycle_id == cycle_id).options(joinedload(Exam.subject))).all()
        )
        slots_list = list(db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle_id)).all())

        # Previous slot map for disruption minimization
        prior_slot_map = {a.exam_id: a.time_slot_id for a in source_ver.assignments}

        exams_dict_info = {
            e.id: ExamInfo(
                id=e.id,
                subject_code=e.subject.subject_code,
                duration_minutes=e.duration_minutes,
                restricted_dates=e.restricted_dates or [],
                preferred_dates=e.preferred_dates or [],
                locked_slot_id=locked_exam_map.get(e.id),
                prior_slot_id=prior_slot_map.get(e.id) if req.minimizeDisruption else None,
            )
            for e in exams_list
        }
        slots_info = [
            SlotInfo(
                id=s.id,
                date=s.date,
                start_time=s.start_time.strftime("%H:%M") if hasattr(s.start_time, "strftime") else str(s.start_time),
                end_time=s.end_time.strftime("%H:%M") if hasattr(s.end_time, "strftime") else str(s.end_time),
                duration_minutes=s.duration_minutes,
                slot_index=s.slot_index,
                session_label=s.session_label,
                is_enabled=s.enabled,
            )
            for s in slots_list
        ]

        color_classes: dict[int, list[str]] = {}
        for eid, c in coloring_result.colors.items():
            color_classes.setdefault(c, []).append(eid)

        mapping_result = map_colors_to_slots(
            color_classes=color_classes,
            slots=slots_info,
            exams=exams_dict_info,
        )

        if not mapping_result.is_feasible:
            raise DomainException(
                code="REGENERATION_INFEASIBLE",
                message=f"Regeneration infeasible: {mapping_result.message}",
                status_code=422,
            )

        # 7. Form new assignments and validate
        new_assignments_payload: list[dict[str, Any]] = []
        for eid, c in coloring_result.colors.items():
            sid = mapping_result.color_to_slot[c]
            new_assignments_payload.append({
                "exam_id": eid,
                "time_slot_id": sid,
                "color_id": c,
                "locked": (eid in locked_exam_map),
            })

        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle_id,
                )
            ).all()
        )
        enrollments_tuples: list[tuple[str, str]] = [(str(r[0]), str(r[1])) for r in enrollments]

        exams_dict = {
            e.id: {
                "id": e.id,
                "subject_code": e.subject.subject_code,
                "duration_minutes": e.duration_minutes,
                "restricted_dates": e.restricted_dates or [],
                "preferred_dates": e.preferred_dates or [],
                "cycle_id": e.scheduling_cycle_id,
                "locked_slot_id": locked_exam_map.get(e.id),
            }
            for e in exams_list
        }
        slots_dict = {
            s.id: {
                "id": s.id,
                "date": s.date,
                "start_time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, "strftime") else str(s.start_time),
                "end_time": s.end_time.strftime("%H:%M") if hasattr(s.end_time, "strftime") else str(s.end_time),
                "duration_minutes": s.duration_minutes,
                "is_enabled": s.enabled,
                "slot_index": s.slot_index,
                "session_label": s.session_label,
                "cycle_id": s.scheduling_cycle_id,
            }
            for s in slots_list
        }

        validation_report = validate_schedule(
            exams=exams_dict,
            slots=slots_dict,
            assignments=new_assignments_payload,
            enrollments=enrollments_tuples,
            cycle_id=cycle_id,
        )

        cycle = db.get(SchedulingCycle, cycle_id)
        weights = (cycle.configuration_json or {}).get("softConstraintWeights", {}) if cycle else {}
        soft_penalty, soft_breakdown = evaluate_soft_constraints(
            assignments=new_assignments_payload,
            slots=slots_dict,
            exams=exams_dict,
            enrollments=enrollments_tuples,
            weights=weights,
        )

        # 8. Create NEW Candidate ScheduleVersion (P9.18)
        max_ver = db.scalar(
            select(func.max(ScheduleVersion.version_number))
            .where(ScheduleVersion.scheduling_cycle_id == cycle_id)
        ) or 0
        new_version_num = max_ver + 1

        new_version = ScheduleVersion(
            scheduling_cycle_id=cycle_id,
            version_number=new_version_num,
            schedule_run_id=source_ver.schedule_run_id,
            status=ScheduleStatus.CANDIDATE,
            soft_score=soft_penalty,
            validation_report_json={
                "valid": validation_report.valid,
                "hardViolations": [
                    {
                        "type": v.type,
                        "examIds": v.exam_ids,
                        "slotId": v.slot_id,
                        "message": v.message,
                        "sharedStudentCount": v.shared_student_count,
                    }
                    for v in validation_report.hard_violations
                ],
                "softPenaltyTotal": soft_penalty,
                "softBreakdown": [
                    {
                        "rule": getattr(sb, "rule", sb.get("rule") if isinstance(sb, dict) else ""),
                        "weight": getattr(sb, "weight", sb.get("weight") if isinstance(sb, dict) else 0.0),
                        "count": getattr(sb, "count", sb.get("count") if isinstance(sb, dict) else 0),
                        "penalty": getattr(sb, "penalty", sb.get("penalty") if isinstance(sb, dict) else 0.0),
                        "message": getattr(sb, "message", sb.get("message") if isinstance(sb, dict) else ""),
                    }
                    for sb in soft_breakdown
                ],
                "warnings": validation_report.warnings,
            },
            row_version=1,
            created_by=actor.id,
        )
        db.add(new_version)
        db.flush()

        for a in new_assignments_payload:
            db.add(
                ExamAssignment(
                    schedule_version_id=new_version.id,
                    exam_id=a["exam_id"],
                    time_slot_id=a["time_slot_id"],
                    color_id=a["color_id"],
                    locked=a["locked"],
                    manual_override=False,
                )
            )

        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_REGENERATE,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=new_version.id,
            after={
                "sourceVersionId": source_ver.id,
                "newVersionNumber": new_version_num,
                "algorithm": algo,
                "preserveLockedExams": req.preserveLockedExams,
                "minimizeDisruption": req.minimizeDisruption,
                "lockedCount": len(locked_exam_map),
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_version)
        return ScheduleVersionService.get_version(db, new_version.id)

    @staticmethod
    def get_change_impact_report(
        db: Session,
        new_version_id: str,
        old_version_id: str,
    ) -> ChangeImpactReportResponse:
        """Computes change impact report diffing old and new schedule versions (Task P9.19)."""
        old_ver = ScheduleVersionService.get_version(db, old_version_id)
        new_ver = ScheduleVersionService.get_version(db, new_version_id)

        old_map = {a.exam_id: a for a in old_ver.assignments}
        new_map = {a.exam_id: a for a in new_ver.assignments}

        moved_exams: list[MovedExamItem] = []
        unchanged_count = 0
        locked_preserved_count = 0

        for eid, new_a in new_map.items():
            old_a = old_map.get(eid)
            if not old_a:
                continue

            if old_a.locked and new_a.time_slot_id == old_a.time_slot_id:
                locked_preserved_count += 1

            if new_a.time_slot_id == old_a.time_slot_id:
                unchanged_count += 1
            else:
                moved_exams.append(
                    MovedExamItem(
                        exam_id=eid,
                        subject_code=new_a.exam.subject.subject_code,
                        subject_name=new_a.exam.subject.subject_name,
                        from_slot_id=old_a.time_slot_id,
                        from_slot_date=str(old_a.time_slot.date),
                        from_slot_session=old_a.time_slot.session_label or "",
                        to_slot_id=new_a.time_slot_id,
                        to_slot_date=str(new_a.time_slot.date),
                        to_slot_session=new_a.time_slot.session_label or "",
                    )
                )

        new_exams_added = [eid for eid in new_map if eid not in old_map]
        exams_removed = [eid for eid in old_map if eid not in new_map]

        old_val = (old_ver.validation_report_json or {}).get("valid", True)
        new_val = (new_ver.validation_report_json or {}).get("valid", True)

        return ChangeImpactReportResponse(
            old_version_id=old_ver.id,
            new_version_id=new_ver.id,
            exams_moved_count=len(moved_exams),
            exams_unchanged_count=unchanged_count,
            locked_preserved_count=locked_preserved_count,
            old_soft_score=old_ver.soft_score,
            new_soft_score=new_ver.soft_score,
            soft_score_delta=round(new_ver.soft_score - old_ver.soft_score, 4),
            old_hard_valid=old_val,
            new_hard_valid=new_val,
            moved_exams=moved_exams,
            new_exams_added=new_exams_added,
            exams_removed=exams_removed,
        )


schedule_version_service = ScheduleVersionService()
