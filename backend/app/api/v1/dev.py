"""Development and Demonstration Endpoints (PRD §32, Task P16.4).

Provides administrator utilities in non-production environments to seed demo datasets.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.config.settings import get_settings
from app.models.enums import RoleEnum
from app.models.user import User
from app.scripts.seed_demo import run_demo_seed

router = APIRouter(prefix="/dev", tags=["Development & Demo"])


@router.get("/status", summary="Check demo tools availability")
def get_demo_status(
    actor: User = Depends(require_role(RoleEnum.ADMIN)),
) -> dict[str, Any]:
    settings = get_settings()
    is_prod = getattr(settings, "APP_ENV", "development").lower() in ["prod", "production"]
    return {
        "demoSeedingAllowed": not is_prod,
        "environment": settings.APP_ENV,
    }


@router.post(
    "/seed-demo",
    summary="Seed comprehensive demonstration dataset (non-production only)",
    status_code=status.HTTP_200_OK,
)
def seed_demo_data(
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN)),
) -> dict[str, Any]:
    settings = get_settings()
    app_env = getattr(settings, "APP_ENV", "development").lower()
    if app_env in ["prod", "production"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo data seeding is strictly disabled in production environments.",
        )

    try:
        summary = run_demo_seed(db=db)
        return {
            "success": True,
            "message": "Demonstration dataset seeded successfully.",
            "data": summary,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed demo data: {exc}",
        ) from exc
