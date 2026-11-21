"""Publishing, Timetables, PDF/Excel Exports, and Reports API Router.

PRD §16, §18.7, §20, §21, §23, Tasks P10.1 - P10.21.
"""

from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.enums import AuditAction, RoleEnum
from app.models.user import User
from app.schemas.publishing_reporting import (
    AuditLogListResponse,
    CycleReportSummaryResponse,
    MasterTimetableResponse,
    PublishScheduleRequest,
    ScheduleDistributionResponse,
    StudentTimetableResponse,
)
from app.schemas.schedule_version import ScheduleVersionDetailResponse
from app.services.publishing_service import publishing_service

router = APIRouter(tags=["Publishing & Timetables"])


@router.post(
    "/schedules/{version_id}/publish",
    response_model=ScheduleVersionDetailResponse,
    summary="Publish timetable version making it official and immutable (P10.1 - P10.4)",
)
def publish_schedule(
    version_id: str,
    req: PublishScheduleRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN)),
    request: Request = None,  # type: ignore[assignment]
) -> ScheduleVersionDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    ver = publishing_service.publish_schedule(
        db=db,
        version_id=version_id,
        req=req,
        actor=actor,
        request_id=request_id,
    )
    from app.api.v1.schedule_versions import _map_version_detail
    return _map_version_detail(db, ver)


@router.get(
    "/me/timetable",
    response_model=StudentTimetableResponse,
    summary="Authenticated student convenience endpoint for individual timetable (P10.6)",
)
def get_my_timetable(
    cycle_id: str | None = Query(default=None, description="Optional cycle ID (defaults to active published cycle)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentTimetableResponse:
    return publishing_service.get_my_timetable(db=db, actor=current_user, cycle_id=cycle_id)


@router.get(
    "/students/{student_id}/timetable",
    response_model=StudentTimetableResponse,
    summary="Get individual timetable for a student with privacy scoping (P10.5, P10.8)",
)
def get_student_timetable(
    student_id: str,
    cycle_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentTimetableResponse:
    return publishing_service.get_student_timetable(
        db=db,
        student_id=student_id,
        cycle_id=cycle_id,
        actor=current_user,
    )


@router.get(
    "/schedules/{version_id}/timetable/master",
    response_model=MasterTimetableResponse,
    summary="Get master examination timetable with department, date, and session filters (P10.7)",
)
def get_master_timetable(
    version_id: str,
    department_id: str | None = Query(default=None),
    date: str | None = Query(default=None),
    session_label: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY)),
) -> MasterTimetableResponse:
    return publishing_service.get_master_timetable(
        db=db,
        version_id=version_id,
        department_id=department_id,
        date_filter=date,
        session_label=session_label,
        actor=current_user,
    )


@router.get(
    "/schedules/{version_id}/export/csv",
    summary="Download RFC 4180 CSV examination timetable with formula injection neutralization (P10.9, P10.14)",
)
def export_csv(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY)),
) -> Response:
    csv_content = publishing_service.generate_csv_export(db=db, version_id=version_id, actor=current_user)
    filename = f"timetable_{version_id}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/schedules/{version_id}/export/pdf",
    summary="Download publication-quality PDF examination timetable (P10.10, P10.14)",
)
def export_pdf(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY)),
) -> StreamingResponse:
    pdf_bytes = publishing_service.generate_pdf_export(db=db, version_id=version_id, actor=current_user)
    filename = f"timetable_{version_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/schedules/{version_id}/export/excel",
    summary="Download multi-tab Excel examination timetable workbook (P10.11, P10.14)",
)
def export_excel(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY)),
) -> StreamingResponse:
    excel_bytes = publishing_service.generate_excel_export(db=db, version_id=version_id, actor=current_user)
    filename = f"timetable_{version_id}.xlsx"
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/cycles/{cycle_id}/reports/summary",
    response_model=CycleReportSummaryResponse,
    summary="Get cycle summary metrics and statistics report (P10.15)",
)
def get_cycle_summary_report(
    cycle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> CycleReportSummaryResponse:
    return publishing_service.get_cycle_summary_report(db, cycle_id)


@router.get(
    "/schedules/{version_id}/reports/distribution",
    response_model=ScheduleDistributionResponse,
    summary="Get workload distribution report across dates, sessions, and students (P10.16)",
)
def get_schedule_distribution_report(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
) -> ScheduleDistributionResponse:
    return publishing_service.get_schedule_distribution_report(db, version_id)


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Query system audit log trail with administrative filters (P10.20)",
)
def get_audit_logs(
    action: AuditAction | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    actor_email: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
) -> AuditLogListResponse:
    return publishing_service.get_audit_logs(
        db=db,
        action=action,
        entity_type=entity_type,
        actor_email=actor_email,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
