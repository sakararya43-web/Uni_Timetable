
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.student import PaginatedStudentsResponse
from app.schemas.subject import (
    PaginatedSubjectsResponse,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from app.services.subject_service import subject_service

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("", response_model=PaginatedSubjectsResponse)
def get_subjects(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    departmentId: str | None = Query(default=None, alias="departmentId"),
    programId: str | None = Query(default=None, alias="programId"),
    semester: int | None = Query(default=None, ge=1, le=16),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedSubjectsResponse:
    items, total, total_pages = subject_service.get_subjects_paginated(
        db=db,
        actor=current_user,
        page=page,
        page_size=pageSize,
        department_id=departmentId,
        program_id=programId,
        semester=semester,
        status=status,
        search=search,
    )
    return PaginatedSubjectsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    return subject_service.create_subject(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    return subject_service.get_subject_by_id(db=db, subject_id=subject_id, actor=current_user)


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    return subject_service.update_subject(
        db=db,
        subject_id=subject_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )


@router.delete("/{subject_id}", response_model=SubjectResponse)
def archive_subject(
    subject_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    return subject_service.archive_subject(
        db=db,
        subject_id=subject_id,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )


@router.get("/{subject_id}/students", response_model=PaginatedStudentsResponse)
def get_subject_students(
    subject_id: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(
        require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY)
    ),
    db: Session = Depends(get_db),
) -> PaginatedStudentsResponse:
    """Paginated list of students enrolled in this subject (staff only, Task P3.6)."""
    items, total, total_pages = subject_service.get_subject_students(
        db=db,
        subject_id=subject_id,
        actor=current_user,
        page=page,
        page_size=pageSize,
    )
    return PaginatedStudentsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )
