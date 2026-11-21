from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/status", tags=["Status"])
def get_api_v1_status() -> dict:
    return {
        "status": "operational",
        "version": "v1",
        "description": "University Examination Timetable Scheduling System API",
    }


api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
