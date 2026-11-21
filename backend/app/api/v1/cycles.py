
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.scheduling import TimeSlot
from app.models.user import User
from app.schemas.cycle import (
    CapacitySummaryResponse,
    CycleCreate,
    CycleResponse,
    CycleUpdate,
    ExamResponse,
    ExamSyncResponse,
    ExamUpdate,
    PaginatedCyclesResponse,
    PaginatedExamsResponse,
    PaginatedSlotsResponse,
    TimeSlotResponse,
)
from app.services.cycle_service import cycle_service
from app.services.slot_service import slot_service

router = APIRouter(prefix="/cycles", tags=["Scheduling Cycles"])


# ==============================================================================
# 1. Cycle Management Endpoints (Task P5.1)
# ==============================================================================
@router.get("", response_model=PaginatedCyclesResponse)
def get_cycles(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    academicYearId: str | None = Query(default=None, alias="academicYearId"),
    semesterId: str | None = Query(default=None, alias="semesterId"),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedCyclesResponse:
    items, total, total_pages = cycle_service.get_cycles_paginated(
        db=db,
        page=page,
        page_size=pageSize,
        academic_year_id=academicYearId,
        semester_id=semesterId,
        status=status,
        search=search,
    )
    return PaginatedCyclesResponse(
        items=[CycleResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
def create_cycle(
    data: CycleCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> CycleResponse:
    cycle = cycle_service.create_cycle(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return CycleResponse.model_validate(cycle)


@router.get("/{cycle_id}", response_model=CycleResponse)
def get_cycle(
    cycle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CycleResponse:
    cycle = cycle_service.get_cycle_by_id(db=db, cycle_id=cycle_id)
    return CycleResponse.model_validate(cycle)


@router.patch("/{cycle_id}", response_model=CycleResponse)
def update_cycle(
    cycle_id: str,
    data: CycleUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> CycleResponse:
    cycle = cycle_service.update_cycle(
        db=db,
        cycle_id=cycle_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
    return CycleResponse.model_validate(cycle)


@router.delete("/{cycle_id}", response_model=CycleResponse)
def archive_cycle(
    cycle_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> CycleResponse:
    cycle = cycle_service.archive_cycle(
        db=db, cycle_id=cycle_id, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return CycleResponse.model_validate(cycle)


# ==============================================================================
# 2. Exam Synchronization & Overrides (Tasks P5.4, P5.5)
# ==============================================================================
@router.post("/{cycle_id}/exams/sync", response_model=ExamSyncResponse)
def sync_exams(
    cycle_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> ExamSyncResponse:
    """Synchronize exams from active subjects matching cycle scope (Task P5.4)."""
    return cycle_service.sync_exams(
        db=db, cycle_id=cycle_id, actor=current_user, request_id=request_id_ctx_var.get()
    )


@router.get("/{cycle_id}/exams", response_model=PaginatedExamsResponse)
def get_cycle_exams(
    cycle_id: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedExamsResponse:
    items, total, total_pages = cycle_service.get_cycle_exams_paginated(
        db=db, cycle_id=cycle_id, page=page, page_size=pageSize
    )
    return PaginatedExamsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.patch("/{cycle_id}/exams/{exam_id}", response_model=ExamResponse)
def update_exam(
    cycle_id: str,
    exam_id: str,
    data: ExamUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> ExamResponse:
    """Update per-exam overrides (duration, priority, dates) (Task P5.5)."""
    return cycle_service.update_exam_override(
        db=db,
        exam_id=exam_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )


# ==============================================================================
# 3. Slot Generation & Inspection (Tasks P5.9, P5.10, P5.11)
# ==============================================================================
@router.post("/{cycle_id}/slots/generate", response_model=list[TimeSlotResponse])
def generate_slots(
    cycle_id: str,
    force: bool = Query(default=False, description="Force regeneration even if assignments exist"),
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> list[TimeSlotResponse]:
    """Generate time slots from cycle calendar and session rules (Task P5.9)."""
    return slot_service.save_generated_slots(
        db=db,
        cycle_id=cycle_id,
        actor=current_user,
        force=force,
        request_id=request_id_ctx_var.get(),
    )


@router.get("/{cycle_id}/slots", response_model=PaginatedSlotsResponse)
def get_cycle_slots(
    cycle_id: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200, alias="pageSize"),
    enabled: bool | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedSlotsResponse:
    """List time slots for cycle (Task P5.10)."""
    query = select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle_id)
    if enabled is not None:
        query = query.where(TimeSlot.enabled == enabled)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    total_pages = (total + pageSize - 1) // pageSize if total > 0 else 1

    offset = (page - 1) * pageSize
    slots = list(
        db.scalars(
            query.order_by(TimeSlot.slot_index.asc()).offset(offset).limit(pageSize)
        ).all()
    )

    items = [
        TimeSlotResponse(
            id=s.id,
            scheduling_cycle_id=s.scheduling_cycle_id,
            date=s.date,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            duration_minutes=s.duration_minutes,
            session_label=s.session_label,
            slot_index=s.slot_index,
            enabled=s.enabled,
            capacity=s.capacity,
        )
        for s in slots
    ]

    return PaginatedSlotsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.get("/{cycle_id}/slots/capacity-summary", response_model=CapacitySummaryResponse)
def get_capacity_summary(
    cycle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CapacitySummaryResponse:
    """Slot capacity metrics and chromatic lower-bound feasibility pre-check (Task P5.11)."""
    return slot_service.get_capacity_summary(db=db, cycle_id=cycle_id)
