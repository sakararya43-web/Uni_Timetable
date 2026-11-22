from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.router import api_v1_router
from app.config.database import get_db
from app.config.logging import setup_logging
from app.config.settings import Settings, get_settings
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import (
    IdempotencyMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    setup_logging(debug=settings.DEBUG)

    # OpenAPI docs toggled by environment / debug
    docs_url = "/docs" if settings.DEBUG or settings.APP_ENV != "production" else None
    redoc_url = "/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None

    tags_metadata = [
        {
            "name": "System Health",
            "description": "Liveness, readiness, and service telemetry endpoints.",
        },
        {"name": "Status", "description": "API status, versioning, and environment metadata."},
        {
            "name": "Authentication",
            "description": "User login, refresh tokens, and session denylist.",
        },
        {
            "name": "Academic Structure",
            "description": "Departments, academic years, semesters, programs.",
        },
        {
            "name": "Scheduling Cycles",
            "description": "Cycle configuration, slot generation, and state transitions.",
        },
        {
            "name": "Conflict Graph",
            "description": "Pure conflict graph engine, chromatic bounds, and snapshots.",
        },
        {
            "name": "Schedule Engine",
            "description": "Coloring algorithms (DSATUR, Welsh-Powell, Greedy) and timetable mapping.",
        },
    ]

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "Enterprise University Examination Timetable Scheduling System API "
            "using Graph Coloring algorithms."
        ),
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url="/openapi.json" if docs_url else None,
        openapi_tags=tags_metadata,
        contact={
            "name": "Academic Examination Scheduling Registry",
            "email": "registrar@university.edu",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Middlewares (ordered: outer-most to inner-most)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(RateLimitMiddleware, default_limit=200, window_seconds=60)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error Handlers
    register_error_handlers(app)

    # Health & Readiness Endpoints (PRD Task P1.6)
    @app.get("/health", tags=["System Health"], status_code=status.HTTP_200_OK)
    def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @app.get("/ready", tags=["System Health"], status_code=status.HTTP_200_OK)
    def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
        try:
            # Verify database connectivity
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"unreachable: {str(e)}"

        return {
            "status": "ready" if db_status == "connected" else "degraded",
            "database": db_status,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # Mount API v1 router
    app.include_router(api_v1_router)

    return app


app = create_app()
