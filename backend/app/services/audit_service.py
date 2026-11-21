import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction

logger = logging.getLogger("exam_scheduler")

# Sensitive fields stripped/redacted from audit records (PRD FR-21, Task P2.21)
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "csrf_token",
}


def redact_sensitive_data(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Deep redaction utility removing passwords and secrets from dictionaries."""
    if data is None:
        return None

    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            redacted[key] = value

    return redacted


class AuditService:
    """Transparent audit logging service (FR-21, Task P2.20)."""

    @staticmethod
    def record(
        db: Session,
        action: AuditAction,
        entity_type: str,
        actor_email: str,
        actor_id: str | None = None,
        entity_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        audit_entry = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            before_state=redact_sensitive_data(before),
            after_state=redact_sensitive_data(after),
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        db.add(audit_entry)
        # Flush to generate ID without committing outer transaction
        db.flush()
        return audit_entry


audit_service = AuditService()
