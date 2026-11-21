from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")


# Placeholder for route modules mounted in subsequent phases (Phase 2 to 10)
@api_v1_router.get("/status", tags=["Status"])
def get_api_v1_status() -> dict:
    return {
        "status": "operational",
        "version": "v1",
        "description": "University Examination Timetable Scheduling System API",
    }
