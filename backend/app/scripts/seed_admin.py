import sys

from sqlalchemy import select

from app.config.database import SessionLocal
from app.config.settings import get_settings
from app.models.enums import AuditAction, RoleEnum, UserStatus
from app.models.user import User
from app.services.audit_service import audit_service
from app.utils.security import hash_password


def seed_admin() -> None:
    """Seed initial administrative user from environment variables (Task P2.13)."""
    settings = get_settings()
    db = SessionLocal()
    try:
        email = settings.ADMIN_EMAIL.lower().strip()
        existing = db.scalar(select(User).where(User.email == email))

        if existing:
            print(f"[seed_admin] Admin user '{email}' already exists (ID: {existing.id}).")
            return

        admin_user = User(
            email=email,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            full_name=settings.ADMIN_FULL_NAME,
            role=RoleEnum.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin_user)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            actor_email="system_seed",
            entity_id=admin_user.id,
            after={"email": admin_user.email, "role": admin_user.role.value, "seeded": True},
        )
        db.commit()
        print(
            f"[seed_admin] Successfully created initial Administrator: '{email}' (ID: {admin_user.id})"
        )
    except Exception as e:
        db.rollback()
        print(f"[seed_admin] Error seeding admin user: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
