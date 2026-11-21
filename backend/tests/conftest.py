import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.database import Base, get_db
from app.config.settings import Settings, get_settings
from app.main import create_app

# Use an isolated SQLite file for local/isolated unit tests
TEST_DB_URL = "sqlite:///./test_scheduler.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        DEBUG=True,
        DATABASE_URL=TEST_DB_URL,
        JWT_SECRET="test_secret_key_minimum_32_characters_long_for_security",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_scheduler.db"):
        try:
            os.remove("./test_scheduler.db")
        except OSError:
            pass


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    test_settings = override_get_settings()
    app = create_app(test_settings)

    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client
