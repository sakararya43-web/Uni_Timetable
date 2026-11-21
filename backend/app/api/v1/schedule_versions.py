"""Schedule Version Management, Manual Editing, Locking, and Regeneration API Router.

PRD §15, §17.14, §17.15, §18.7, Tasks P9.1 - P9.21.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.audit import AuditLog
from app.models.enums import RoleEnum
from app.models.schedule import ExamAssignment, ScheduleVersion
from app.models.user import User
from app.schemas.schedule import (
    HardViolationSchema,
    ScheduleValidationReportSchema,
    SoftBreakdownSchema,
)
from app.schemas.schedule_version import (
    AssignmentDetailResponse,
    BulkLockRequest,
    ChangeImpactReportResponse,
    LockValidationResponse,
    PreviewMoveRequest,
    PreviewMoveResponse,
    ScheduleRegenerateRequest,
    ScheduleVersionDetailResponse,
    ScheduleVersionListItem,
    SwapAssignmentsRequest,
    UpdateAssignmentRequest,
)
from app.services.schedule_version_service import schedule_version_service

router = APIRouter(tags=["Schedule Versions & Editing"])


def _map_assignment_detail(a: ExamAssignment) -> AssignmentDetailResponse:
    sub = a.exam.subject if a.exam and a.exam.subject else None
    dept = sub.department if sub and sub.department else None
    slot = a.time_slot

    start_str = slot.start_time.strftime("%H:%M") if slot and hasattr(slot.start_time, "strftime") else str(slot.start_time) if slot else None
    end_str = slot.end_time.strftime("%H:%M") if slot and hasattr(slot.end_time, "strftime") else str(slot.end_time) if slot else None

    return AssignmentDetailResponse(
        id=a.id,
        schedule_version_id=a.schedule_version_id,
        exam_id=a.exam_id,
        time_slot_id=a.time_slot_id,
        color_id=a.color_id,
        locked=a.locked,
        manual_override=a.manual_override,
        subject_id=sub.id if sub else None,
        subject_code=sub.subject_code if sub else None,
        subject_name=sub.subject_name if sub else None,
        department_code=dept.code if dept else None,
        duration_minutes=a.exam.duration_minutes if a.exam else None,
        slot_date=slot.date if slot else None,
        slot_start_time=start_str,
        slot_end_time=end_str,
        slot_duration_minutes=slot.duration_minutes if slot else None,
        slot_index=slot.slot_index if slot else None,
        session_label=slot.session_label if slot else None,
    )


def _map_version_detail(db: Session, ver: ScheduleVersion) -> ScheduleVersionDetailResponse:
    val_data = ver.validation_report_json or {}
    val_schema = ScheduleValidationReportSchema(
        valid=val_data.get("valid", True),
        hard_violations=[HardViolationSchema(**hv) for hv in val_data.get("hardViolations", [])],
        soft_penalty_total=val_data.get("softPenaltyTotal", 0.0),
        soft_breakdown=[SoftBreakdownSchema(**sb) for sb in val_data.get("softBreakdown", [])],
        warnings=val_data.get("warnings", []),
    )

    # Load audit history
    audit_rows = list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.entity_id == ver.id)
            .order_by(AuditLog.timestamp.desc())
            .limit(50)
        ).all()
    )
    edit_history = [
        {
            "id": r.id,
            "action": r.action,
            "actorId": r.actor_id,
            "createdAt": r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
            "details": r.after_state,
        }
        for r in audit_rows
    ]

    assignments_detail = [_map_assignment_detail(a) for a in ver.assignments]

    return ScheduleVersionDetailResponse(
        id=ver.id,
        scheduling_cycle_id=ver.scheduling_cycle_id,
        version_number=ver.version_number,
        schedule_run_id=ver.schedule_run_id,
        status=ver.status,
        published_at=ver.published_at,
        soft_score=ver.soft_score,
        row_version=ver.row_version,
        assignments=assignments_detail,
        validation_report=val_schema,
        edit_history=edit_history,
        created_at=ver.created_at,
        updated_at=ver.updated_at,
    )


@router.get(
    "/cycles/{cycle_id}/schedules",
    response_model=list[ScheduleVersionListItem],
    summary="List all timetable versions for a scheduling cycle (Task P9.1)",
)
def list_cycle_schedules(
    cycle_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> list[ScheduleVersionListItem]:
    versions = schedule_version_service.list_cycle_schedules(db, cycle_id)
    result: list[ScheduleVersionListItem] = []
    for v in versions:
        val_data = v.validation_report_json or {}
        result.append(
            ScheduleVersionListItem(
                id=v.id,
                scheduling_cycle_id=v.scheduling_cycle_id,
                version_number=v.version_number,
                schedule_run_id=v.schedule_run_id,
                status=v.status,
                published_at=v.published_at,
                soft_score=v.soft_score,
                row_version=v.row_version,
                assignment_count=len(v.assignments),
                locked_count=len([a for a in v.assignments if a.locked]),
                override_count=len([a for a in v.assignments if a.manual_override]),
                is_valid=val_data.get("valid", True),
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
        )
    return result


@router.get(
    "/schedules/{version_id}",
    response_model=ScheduleVersionDetailResponse,
    summary="Get full timetable version details with assignments, slots, and validation report (Task P9.1)",
)
def get_schedule_version(
    version_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> ScheduleVersionDetailResponse:
    ver = schedule_version_service.get_version(db, version_id)
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/clone",
    response_model=ScheduleVersionDetailResponse,
    summary="Clone a schedule version (even Published) into a new editable Candidate version (Task P9.2)",
)
def clone_schedule_version(
    version_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    new_ver = schedule_version_service.clone_version(db, version_id, actor, request_id)
    return _map_version_detail(db, new_ver)


@router.post(
    "/schedules/{version_id}/archive",
    response_model=ScheduleVersionDetailResponse,
    summary="Archive a schedule version (Task P9.4)",
)
def archive_schedule_version(
    version_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.archive_version(db, version_id, actor, request_id)
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/assignments/{assignment_id}/preview-move",
    response_model=PreviewMoveResponse,
    summary="Dry-run preview of moving an exam to a target slot with conflict analysis and soft score delta (Task P9.5, P9.7)",
)
def preview_assignment_move(
    version_id: str,
    assignment_id: str,
    req: PreviewMoveRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> PreviewMoveResponse:
    return schedule_version_service.preview_assignment_move(
        db=db,
        version_id=version_id,
        assignment_id=assignment_id,
        target_slot_id=req.timeSlotId,
    )


@router.patch(
    "/schedules/{version_id}/assignments/{assignment_id}",
    response_model=ScheduleVersionDetailResponse,
    summary="Move an exam assignment to a target slot with optimistic concurrency and validation (Task P9.6, P9.8, P9.10, P9.11)",
)
def move_assignment(
    version_id: str,
    assignment_id: str,
    req: UpdateAssignmentRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.move_assignment(
        db=db,
        version_id=version_id,
        assignment_id=assignment_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/assignments/swap",
    response_model=ScheduleVersionDetailResponse,
    summary="Atomically swap time slots between two exam assignments (Task P9.9)",
)
def swap_assignments(
    version_id: str,
    req: SwapAssignmentsRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.swap_assignments(
        db=db,
        version_id=version_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/assignments/{assignment_id}/lock",
    response_model=ScheduleVersionDetailResponse,
    summary="Lock an exam to its assigned slot (Task P9.12)",
)
def lock_assignment(
    version_id: str,
    assignment_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.set_assignment_lock(
        db=db,
        version_id=version_id,
        assignment_id=assignment_id,
        locked=True,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/assignments/{assignment_id}/unlock",
    response_model=ScheduleVersionDetailResponse,
    summary="Unlock an exam from its assigned slot (Task P9.12)",
)
def unlock_assignment(
    version_id: str,
    assignment_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.set_assignment_lock(
        db=db,
        version_id=version_id,
        assignment_id=assignment_id,
        locked=False,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/locks/bulk",
    response_model=ScheduleVersionDetailResponse,
    summary="Bulk lock or unlock exam assignments by date or session (Task P9.14)",
)
def bulk_lock_assignments(
    version_id: str,
    req: BulkLockRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = schedule_version_service.bulk_lock_assignments(
        db=db,
        version_id=version_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, ver)


@router.post(
    "/schedules/{version_id}/locks/validate",
    response_model=LockValidationResponse,
    summary="Validate mutual compatibility of all locked exams in a schedule version (Task P9.15)",
)
def validate_locks(
    version_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> LockValidationResponse:
    return schedule_version_service.validate_locks(db, version_id)


@router.post(
    "/schedules/{version_id}/regenerate",
    response_model=ScheduleVersionDetailResponse,
    summary="Regenerate timetable creating a new Candidate version while strictly preserving locked exams and minimizing disruption (Task P9.16 - P9.18)",
)
def regenerate_schedule(
    version_id: str,
    req: ScheduleRegenerateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    new_ver = schedule_version_service.regenerate_schedule(
        db=db,
        version_id=version_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )
    return _map_version_detail(db, new_ver)


@router.get(
    "/schedules/{new_version_id}/diff/{old_version_id}",
    response_model=ChangeImpactReportResponse,
    summary="Change impact report comparing old and new schedule versions (Task P9.19)",
)
def get_change_impact_report(
    new_version_id: str,
    old_version_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> ChangeImpactReportResponse:
    return schedule_version_service.get_change_impact_report(
        db=db,
        new_version_id=new_version_id,
        old_version_id=old_version_id,
    )
