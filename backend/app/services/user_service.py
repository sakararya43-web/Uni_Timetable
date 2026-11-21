import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import DomainException
from app.models.enums import AuditAction, UserStatus
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.audit_service import audit_service
from app.utils.security import hash_password


class UserService:
    @staticmethod
    def get_users_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int, int]:
        query = select(User)

        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where((User.email.ilike(pattern)) | (User.full_name.ilike(pattern)))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        items = list(
            db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(page_size)).all()
        )

        return items, total, total_pages

    @staticmethod
    def create_user(
        db: Session,
        data: UserCreateRequest,
        actor: User,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> User:
        # Check duplicate email
        existing = db.scalar(select(User).where(User.email == data.email.lower()))
        if existing:
            raise DomainException(
                code="DUPLICATE_EMAIL",
                message=f"A user with email '{data.email}' already exists.",
                status_code=409,
            )

        new_user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.fullName,
            role=data.role,
            department_id=data.departmentId,
            status=UserStatus.ACTIVE,
        )
        db.add(new_user)
        db.flush()

        role_val = new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role)
        audit_service.record(
            db=db,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=new_user.id,
            after={
                "email": new_user.email,
                "role": role_val,
                "department_id": new_user.department_id,
            },
            ip_address=ip_address,
            request_id=request_id,
        )
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        data: UserUpdateRequest,
        actor: User,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> User:
        user = db.get(User, user_id)
        if not user:
            raise DomainException(code="USER_NOT_FOUND", message="User not found.", status_code=404)

        before_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        before_status = user.status.value if hasattr(user.status, "value") else str(user.status)
        before: dict[str, Any] = {
            "fullName": user.full_name,
            "role": before_role,
            "departmentId": user.department_id,
            "status": before_status,
        }

        if data.fullName is not None:
            user.full_name = data.fullName
        if data.role is not None:
            user.role = data.role
        if data.departmentId is not None:
            user.department_id = data.departmentId
        if data.status is not None:
            user.status = data.status

        after_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        after_status = user.status.value if hasattr(user.status, "value") else str(user.status)
        after: dict[str, Any] = {
            "fullName": user.full_name,
            "role": after_role,
            "departmentId": user.department_id,
            "status": after_status,
        }

        audit_service.record(
            db=db,
            action=AuditAction.USER_UPDATE,
            entity_type="user",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=user.id,
            before=before,
            after=after,
            ip_address=ip_address,
            request_id=request_id,
        )
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def reset_password(
        db: Session,
        user_id: str,
        new_password: str,
        actor: User,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        user = db.get(User, user_id)
        if not user:
            raise DomainException(code="USER_NOT_FOUND", message="User not found.", status_code=404)

        user.password_hash = hash_password(new_password)
        user.failed_login_count = 0
        user.locked_until = None

        audit_service.record(
            db=db,
            action=AuditAction.USER_PASSWORD_RESET,
            entity_type="user",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=user.id,
            ip_address=ip_address,
            request_id=request_id,
        )
        db.commit()


user_service = UserService()
