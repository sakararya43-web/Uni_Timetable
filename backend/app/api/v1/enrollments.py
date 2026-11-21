
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentValidationReport,
    PaginatedEnrollmentsResponse,
)
from app.services.enrollment_service import enrollment_service

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.get("", response_model=PaginatedEnrollmentsResponse)
def get_enrollments(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    studentId: str | None = Query(default=None, alias="studentId"),
    subjectId: str | None = Query(default=None, alias="subjectId"),
    cycleId: str | None = Query(default=None, alias="cycleId"),
    status: str | None = Query(default=None),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> PaginatedEnrollmentsResponse:
    items, total, total_pages = enrollment_service.get_enrollments_paginated(
        db=db,
        actor=current_user,
        page=page,
        page_size=pageSize,
        student_id=studentId,
        subject_id=subjectId,
        cycle_id=cycleId,
        status=status,
    )
    return PaginatedEnrollmentsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.get("/validate", response_model=EnrollmentValidationReport)
def validate_enrollments(
    cycleId: str | None = Query(default=None, alias="cycleId"),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> EnrollmentValidationReport:
    """Diagnostic reporting for data anomalies (Task P3.15)."""
    return enrollment_service.validate_enrollments_integrity(
        db=db, actor=current_user, cycle_id=cycleId
    )


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    data: EnrollmentCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    return enrollment_service.create_enrollment(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )


@router.delete("/{enrollment_id}", response_model=EnrollmentResponse)
def withdraw_enrollment(
    enrollment_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    """Withdraw an enrollment (ADR-003, Task P3.13)."""
    return enrollment_service.withdraw_enrollment(
        db=db,
        enrollment_id=enrollment_id,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
