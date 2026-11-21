from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "University Examination Timetable Scheduling System"
    APP_ENV: str = "development"  # development | test | production
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security & JWT
    JWT_SECRET: str = "default_dev_secret_must_be_changed_in_prod_at_least_32_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./exam_scheduler.db",
        description="Database connection URL. SQLite default for dev/test without Postgres.",
    )
    TEST_DATABASE_URL: str = "sqlite:///./exam_scheduler_test.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            if self.APP_ENV == "production":
                raise ValueError("CORS_ORIGINS cannot be '*' in production!")
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Uploads & Limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_CSV_ROWS: int = 50000

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_GENERATE: str = "10/minute"

    # Initial Admin Seed
    ADMIN_EMAIL: str = "admin@university.edu"
    ADMIN_PASSWORD: str = "AdminChangeMe123!"
    ADMIN_FULL_NAME: str = "System Administrator"


@lru_cache
def get_settings() -> Settings:
    return Settings()
