from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.error_handler import DomainException
from app.models.enums import AuditAction
from app.models.user import TokenDenylist, User
from app.services.audit_service import audit_service
from app.utils.security import create_token, decode_token, verify_password

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> tuple[User, str, int]:
        """Validate credentials with brute-force lockout protection and audit logging."""
        now = datetime.now(UTC)
        stmt = select(User).where(User.email == email.lower().strip())
        user = db.execute(stmt).scalar_one_or_none()

        if user:
            # Check temporary account lockout
            if user.locked_until:
                locked_until = (
                    user.locked_until
                    if user.locked_until.tzinfo
                    else user.locked_until.replace(tzinfo=UTC)
                )
                if locked_until > now:
                    audit_service.record(
                        db=db,
                        action=AuditAction.LOGIN_FAILED,
                        entity_type="user",
                        actor_email=email,
                        actor_id=user.id,
                        entity_id=user.id,
                        after={
                            "reason": "account_locked",
                            "locked_until": locked_until.isoformat(),
                        },
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_id=request_id,
                    )
                    db.commit()
                    raise DomainException(
                        code="ACCOUNT_LOCKED",
                        message="Account is temporarily locked due to excessive failed attempts. Please try again later.",
                        status_code=429,
                    )

        # Constant-time comparison check
        valid_password = False
        if user:
            valid_password = verify_password(password, user.password_hash)

        if not user or not valid_password:
            if user:
                user.failed_login_count += 1
                if user.failed_login_count >= MAX_FAILED_LOGINS:
                    user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

                audit_service.record(
                    db=db,
                    action=AuditAction.LOGIN_FAILED,
                    entity_type="user",
                    actor_email=email,
                    actor_id=user.id,
                    entity_id=user.id,
                    after={"failed_count": user.failed_login_count},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                )
                db.commit()

            raise DomainException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
                status_code=401,
            )

        user_status_str = user.status.value if hasattr(user.status, "value") else str(user.status)
        if user_status_str != "active":
            audit_service.record(
                db=db,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                actor_email=email,
                actor_id=user.id,
                entity_id=user.id,
                after={"reason": "inactive_account", "status": user_status_str},
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
            db.commit()
            raise DomainException(
                code="ACCOUNT_INACTIVE",
                message="This account is deactivated. Please contact an administrator.",
                status_code=403,
            )

        # Successful Login
        user.failed_login_count = 0
        user.locked_until = None

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        token, jti, expire = create_token(
            subject=user.id,
            claims={"role": role_str, "email": user.email},
            token_type="access",
        )

        audit_service.record(
            db=db,
            action=AuditAction.LOGIN,
            entity_type="user",
            actor_email=user.email,
            actor_id=user.id,
            entity_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        db.commit()

        expires_in = int((expire - now).total_seconds())
        return user, token, expires_in

    @staticmethod
    def logout_user(
        db: Session,
        token: str,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Invalidate token by recording JTI in denylist."""
        try:
            payload = decode_token(token)
            jti = payload["jti"]
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)

            denylist_entry = TokenDenylist(
                jti=jti,
                user_id=user.id,
                expires_at=exp,
            )
            db.add(denylist_entry)

            audit_service.record(
                db=db,
                action=AuditAction.LOGOUT,
                entity_type="user",
                actor_email=user.email,
                actor_id=user.id,
                entity_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
            db.commit()
        except Exception as e:
            db.rollback()
            raise DomainException(
                code="LOGOUT_FAILED", message="Failed to invalidate session.", status_code=400
            ) from e


auth_service = AuthService()
