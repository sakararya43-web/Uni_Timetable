from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.services.audit_service import audit_service, redact_sensitive_data


def test_sensitive_data_redaction():
    """Verify passwords and tokens are redacted from audit payloads (Task P2.21)."""
    payload = {
        "email": "user@university.edu",
        "password": "SuperSecretPassword123!",
        "password_hash": "argon2id$v=19$...",
        "access_token": "eyJhbGciOi...",
        "nested": {
            "token": "secret_token_val",
            "safe_field": "visible_info",
        },
    }

    redacted = redact_sensitive_data(payload)
    assert redacted is not None
    assert redacted["email"] == "user@university.edu"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["password_hash"] == "[REDACTED]"
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == "visible_info"


def test_audit_service_recording(db_session: Session):
    """Verify audit_service.record persists entry with redacted data (Task P2.20)."""
    audit_service.record(
        db=db_session,
        action=AuditAction.USER_CREATE,
        entity_type="user",
        actor_email="admin@university.edu",
        entity_id="test-entity-123",
        before={"status": "inactive"},
        after={"status": "active", "password": "PlainPasswordToRedact"},
        ip_address="127.0.0.1",
        request_id="req_test_123",
    )
    db_session.commit()

    entry = db_session.scalar(select(AuditLog).where(AuditLog.entity_id == "test-entity-123"))
    assert entry is not None
    assert entry.action == AuditAction.USER_CREATE
    assert entry.actor_email == "admin@university.edu"
    assert entry.request_id == "req_test_123"
    assert entry.after_state["password"] == "[REDACTED]"
    assert entry.after_state["status"] == "active"
