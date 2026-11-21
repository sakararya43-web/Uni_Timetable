"""Schedule Generation, Comparison, and Versioning API Router.

PRD §13, §14, §15, §18.7, Tasks P8.15 - P8.21.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.enums import RoleEnum
from app.models.schedule import ScheduleRun
from app.models.user import User
from app.schemas.schedule import (
    HardViolationSchema,
    ScheduleComparisonResponse,
    ScheduleGenerateRequest,
    ScheduleRunResponse,
    ScheduleValidationReportSchema,
    ScheduleVersionResponse,
    SoftBreakdownSchema,
)
from app.services.schedule_service import schedule_service

router = APIRouter(tags=["Schedule Engine"])


@router.post(
    "/cycles/{cycle_id}/schedule/generate",
    response_model=ScheduleRunResponse,
    status_code=200,
    summary="Generate examination timetable using selected graph coloring algorithm (P8.11, P8.15)",
)
def generate_schedule(
    cycle_id: str,
    req: ScheduleGenerateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleRun:
    request_id = (
        getattr(request.state, "request_id", None)
        if request and hasattr(request, "state")
        else None
    )
    return schedule_service.generate_schedule(
        db=db,
        cycle_id=cycle_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )


@router.post(
    "/cycles/{cycle_id}/schedule/compare",
    response_model=ScheduleComparisonResponse,
    status_code=200,
    summary="Benchmark and compare Greedy, Welsh-Powell, and DSATUR on the same snapshot (P8.18, P8.20)",
)
def compare_algorithms(
    cycle_id: str,
    repeats: int = Query(
        default=3, ge=1, le=10, description="Repetitions for median timing calculation"
    ),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleComparisonResponse:
    request_id = (
        getattr(request.state, "request_id", None)
        if request and hasattr(request, "state")
        else None
    )
    return schedule_service.compare_algorithms(
        db=db,
        cycle_id=cycle_id,
        actor=actor,
        repeats=repeats,
        request_id=request_id,
    )


@router.get(
    "/cycles/{cycle_id}/schedule/runs",
    response_model=list[ScheduleRunResponse],
    summary="List all schedule generation runs for a scheduling cycle (P8.15)",
)
def list_schedule_runs(
    cycle_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY, RoleEnum.STUDENT)
    ),
) -> list[ScheduleRun]:
    return list(
        db.scalars(
            select(ScheduleRun)
            .where(ScheduleRun.scheduling_cycle_id == cycle_id)
            .order_by(ScheduleRun.created_at.desc())
        ).all()
    )


@router.get(
    "/schedule-runs/{run_id}",
    response_model=ScheduleRunResponse,
    summary="Get details of a specific schedule generation run (P8.15)",
)
def get_schedule_run(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY, RoleEnum.STUDENT)
    ),
) -> ScheduleRun:
    run = db.get(ScheduleRun, run_id)
    if not run:
        from app.middleware.error_handler import DomainException

        raise DomainException(
            code="SCHEDULE_RUN_NOT_FOUND", message="Run not found.", status_code=404
        )
    return run


@router.post(
    "/schedule-runs/{run_id}/validate",
    response_model=ScheduleValidationReportSchema,
    summary="Re-run independent validation on a stored schedule run (P8.15)",
)
def validate_schedule_run(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> ScheduleValidationReportSchema:
    return schedule_service.validate_run(db, run_id)


@router.post(
    "/schedule-runs/{run_id}/save",
    response_model=ScheduleVersionResponse,
    summary="Save successful run as candidate schedule version and advance cycle status to Generated (P8.15, P8.16)",
)
def save_run_as_candidate(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionResponse:
    request_id = (
        getattr(request.state, "request_id", None)
        if request and hasattr(request, "state")
        else None
    )
    ver = schedule_service.save_run_as_candidate(
        db=db,
        run_id=run_id,
        actor=actor,
        request_id=request_id,
    )
    val_data = ver.validation_report_json or {}
    val_schema = ScheduleValidationReportSchema(
        valid=val_data.get("valid", True),
        hard_violations=[HardViolationSchema(**hv) for hv in val_data.get("hardViolations", [])],
        soft_penalty_total=val_data.get("softPenaltyTotal", 0.0),
        soft_breakdown=[SoftBreakdownSchema(**sb) for sb in val_data.get("softBreakdown", [])],
        warnings=val_data.get("warnings", []),
    )
    return ScheduleVersionResponse(
        id=ver.id,
        scheduling_cycle_id=ver.scheduling_cycle_id,
        version_number=ver.version_number,
        schedule_run_id=ver.schedule_run_id,
        status=ver.status,
        published_at=ver.published_at,
        soft_score=ver.soft_score,
        assignment_count=len(ver.assignments),
        validation_report=val_schema,
        created_at=ver.created_at,
        updated_at=ver.updated_at,
    )
