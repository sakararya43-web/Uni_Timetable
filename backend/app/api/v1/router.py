from fastapi import APIRouter

from app.api.v1.academic import router as academic_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cycles import router as cycles_router
from app.api.v1.dev import router as dev_router
from app.api.v1.enrollments import router as enrollments_router
from app.api.v1.graph import router as graph_router
from app.api.v1.imports import router as imports_router
from app.api.v1.publishing_reporting import router as publishing_router
from app.api.v1.schedule import router as schedule_router
from app.api.v1.schedule_versions import router as schedule_versions_router
from app.api.v1.students import router as students_router
from app.api.v1.subjects import router as subjects_router
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
api_v1_router.include_router(academic_router)
api_v1_router.include_router(subjects_router)
api_v1_router.include_router(students_router)
api_v1_router.include_router(enrollments_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(cycles_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(schedule_router)
api_v1_router.include_router(schedule_versions_router)
api_v1_router.include_router(publishing_router)
api_v1_router.include_router(dev_router)
