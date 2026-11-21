from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings

settings = get_settings()

# PRD §17 & Task P1.14: Naming conventions for constraints and indices
# Guarantees completely deterministic migration script generation in Alembic.
POSTGRES_INDEX_CONVENTIONS: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_`%(constraint_name)s`",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=POSTGRES_INDEX_CONVENTIONS)


class Base(DeclarativeBase):
    metadata = metadata


# Configure Engine with SQLite vs PostgreSQL compatibility
connect_args: dict[str, Any] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=connect_args,
    pool_pre_ping=True,
    **(
        {}
        if settings.DATABASE_URL.startswith("sqlite")
        else {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
        }
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI per-request database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction() -> Generator[Session, None, None]:
    """Context manager for explicit atomic transaction handling."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
