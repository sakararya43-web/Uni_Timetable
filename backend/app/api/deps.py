from collections.abc import Callable

from fastapi import Cookie, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.middleware.error_handler import DomainException
from app.models.enums import AuditAction, RoleEnum, UserStatus
from app.models.user import TokenDenylist, User
from app.services.audit_service import audit_service
from app.utils.security import decode_token


def extract_token(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> str | None:
    """Extract JWT token from Authorization Bearer header or httpOnly cookie (ADR-001)."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return access_token


def get_current_user(
    request: Request,
    token: str | None = Depends(extract_token),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token, verify denylist, and return authenticated active user."""
    if not token:
        raise DomainException(
            code="UNAUTHORIZED",
            message="Authentication required. Please log in.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        payload = decode_token(token)
    except Exception as e:
        raise DomainException(
            code="UNAUTHORIZED",
            message="Invalid or expired session token. Please log in again.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from e

    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Check token revocation / denylist
    is_revoked = db.scalar(select(TokenDenylist).where(TokenDenylist.jti == jti))
    if is_revoked:
        raise DomainException(
            code="UNAUTHORIZED",
            message="Session has been logged out. Please log in again.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise DomainException(
            code="ACCOUNT_INACTIVE",
            message="User account does not exist or is inactive.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return user


def require_role(*allowed_roles: RoleEnum) -> Callable[..., User]:
    """Dependency factory enforcing Role-Based Access Control (PRD §7, Task P2.15)."""

    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        allowed_str_set = {
            r.value if hasattr(r, "value") else str(r) for r in allowed_roles
        }
        if user_role_str not in allowed_str_set:
            req_id = request_id_ctx_var.get()
            audit_service.record(
                db=db,
                action=AuditAction.ADMIN_OP_FAILED,
                entity_type="authorization",
                actor_email=current_user.email,
                actor_id=current_user.id,
                after={
                    "path": request.url.path,
                    "method": request.method,
                    "required_roles": list(allowed_str_set),
                    "user_role": user_role_str,
                },
                ip_address=request.client.host if request.client else None,
                request_id=req_id,
            )
            db.commit()

            raise DomainException(
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return role_checker


def check_department_scope(user: User, target_department_id: str | None) -> None:
    """Enforce department scoping for coordinators and faculty (Task P2.16)."""
    if user.role == RoleEnum.ADMIN:
        return

    if user.role in (RoleEnum.COORDINATOR, RoleEnum.FACULTY):
        if not user.department_id or user.department_id != target_department_id:
            raise DomainException(
                code="FORBIDDEN",
                message="You are not authorized to view or manage data outside your assigned department.",
                status_code=status.HTTP_403_FORBIDDEN,
            )


def check_student_self_access(user: User, student_user_id: str | None) -> None:
    """Ensure student users can only read their own personal data (Task P2.17)."""
    if user.role == RoleEnum.STUDENT:
        if user.id != student_user_id:
            raise DomainException(
                code="STUDENT_ACCESS_DENIED",
                message="Students are only permitted to access their own academic records.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
