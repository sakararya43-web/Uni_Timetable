from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.database import transaction


def test_database_connectivity(db_session: Session):
    """Verify that queries execute cleanly on the session."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_transaction_context_manager():
    """Verify the transaction context manager commits on success."""
    with transaction() as session:
        val = session.execute(text("SELECT 42")).scalar()
        assert val == 42
