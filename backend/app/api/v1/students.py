from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.student import (
    PaginatedStudentsResponse,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)
from app.schemas.subject import SubjectResponse
from app.services.student_service import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=PaginatedStudentsResponse)
def get_students(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    departmentId: str | None = Query(default=None, alias="departmentId"),
    programId: str | None = Query(default=None, alias="programId"),
    semester: int | None = Query(default=None, ge=1, le=16),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> PaginatedStudentsResponse:
    items, total, total_pages = student_service.get_students_paginated(
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
    return PaginatedStudentsResponse(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> StudentResponse:
    return student_service.create_student(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentResponse:
    return student_service.get_student_by_id(db=db, student_id=student_id, actor=current_user)


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: str,
    data: StudentUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> StudentResponse:
    return student_service.update_student(
        db=db,
        student_id=student_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )


@router.delete("/{student_id}", response_model=StudentResponse)
def archive_student(
    student_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> StudentResponse:
    return student_service.archive_student(
        db=db,
        student_id=student_id,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )


@router.get("/{student_id}/subjects", response_model=list[SubjectResponse])
def get_student_subjects(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SubjectResponse]:
    """List of active subjects in which this student is enrolled (Task P3.10)."""
    return student_service.get_student_subjects(db=db, student_id=student_id, actor=current_user)
