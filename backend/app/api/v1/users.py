from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import MessageResponse, UserProfileResponse
from app.schemas.user import (
    PaginatedUsersResponse,
    PasswordResetRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=PaginatedUsersResponse, status_code=status.HTTP_200_OK)
def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> PaginatedUsersResponse:
    """List system users with pagination and search (Admin only, Task P2.19)."""
    items, total, total_pages = user_service.get_users_paginated(
        db=db,
        page=page,
        page_size=pageSize,
        role=role,
        status=status,
        search=q,
    )

    return PaginatedUsersResponse(
        items=[UserProfileResponse.model_validate(u) for u in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    body: UserCreateRequest,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Create a new user account (Admin only, Task P2.19)."""
    ip_address = request.client.host if request.client else None
    req_id = request_id_ctx_var.get()

    created = user_service.create_user(
        db=db,
        data=body,
        actor=current_user,
        ip_address=ip_address,
        request_id=req_id,
    )
    return UserProfileResponse.model_validate(created)


@router.get("/{user_id}", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
def get_user(
    user_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve user details by ID (Admin only)."""
    user = db.get(User, user_id)
    if not user:
        from app.middleware.error_handler import DomainException

        raise DomainException(code="USER_NOT_FOUND", message="User not found.", status_code=404)
    return UserProfileResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
def update_user(
    request: Request,
    user_id: str,
    body: UserUpdateRequest,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Update role, department, or status of an existing user (Admin only)."""
    ip_address = request.client.host if request.client else None
    req_id = request_id_ctx_var.get()

    updated = user_service.update_user(
        db=db,
        user_id=user_id,
        data=body,
        actor=current_user,
        ip_address=ip_address,
        request_id=req_id,
    )
    return UserProfileResponse.model_validate(updated)


@router.post(
    "/{user_id}/reset-password", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
def reset_user_password(
    request: Request,
    user_id: str,
    body: PasswordResetRequest,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Reset user password (Admin only)."""
    ip_address = request.client.host if request.client else None
    req_id = request_id_ctx_var.get()

    user_service.reset_password(
        db=db,
        user_id=user_id,
        new_password=body.newPassword,
        actor=current_user,
        ip_address=ip_address,
        request_id=req_id,
    )
    return MessageResponse(message="User password has been successfully reset.")
