"""Conflict Graph API Router.

PRD §11 (FR-07), §18.6, §23 (Privacy: no student identities in standard graph endpoints), Tasks P6.11, P6.14.
"""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.graph import (
    ConflictEdgeDetailResponse,
    ConflictGraphResponse,
    GraphBuildResponse,
    GraphStatsResponse,
)
from app.services.graph_service import graph_service

router = APIRouter(prefix="/cycles/{cycle_id}/graph", tags=["Conflict Graph"])


@router.post(
    "/build",
    response_model=GraphBuildResponse,
    status_code=200,
    summary="Build conflict graph snapshot (P6.7, P6.8, P6.9)",
)
def build_graph(
    cycle_id: str,
    force: bool = Query(default=False, description="Force a new snapshot even if enrollment hash is unchanged"),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> GraphBuildResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    snapshot, is_new, validation = graph_service.build_graph_snapshot(
        db=db,
        cycle_id=cycle_id,
        actor=actor,
        force=force,
        request_id=request_id,
    )
    is_stale, _, _ = graph_service.is_cycle_graph_stale(db, cycle_id)
    stats = graph_service.get_graph_stats(db, cycle_id)

    return GraphBuildResponse(
        snapshot_id=snapshot.id,
        cycle_id=cycle_id,
        version=snapshot.version,
        is_new=is_new,
        is_stale=is_stale,
        stats=stats,
        validation=validation,
    )


@router.get(
    "",
    response_model=ConflictGraphResponse,
    summary="Query latest conflict graph (nodes, edges, stats, PII-free) (P6.11)",
)
def get_graph(
    cycle_id: str,
    department_id: str | None = Query(default=None, alias="departmentId"),
    semester: int | None = Query(default=None),
    min_weight: int | None = Query(default=None, alias="minWeight", ge=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY, RoleEnum.STUDENT)),
) -> ConflictGraphResponse:
    return graph_service.get_graph_response(
        db=db,
        cycle_id=cycle_id,
        department_id=department_id,
        semester=semester,
        min_weight=min_weight,
    )


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    summary="Get summary metrics of latest conflict graph (P6.5, P6.11)",
)
def get_graph_stats(
    cycle_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR, RoleEnum.FACULTY, RoleEnum.STUDENT)),
) -> GraphStatsResponse:
    return graph_service.get_graph_stats(db, cycle_id)


@router.get(
    "/export",
    summary="Export conflict graph as JSON or CSV (Admin only, PII-free) (P6.11)",
)
def export_graph(
    cycle_id: str,
    format: str = Query("json", pattern="^(json|csv|JSON|CSV)$"),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN)),
    request: Request = None,  # type: ignore[assignment]
) -> Response:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    content, media_type, filename = graph_service.export_graph(
        db=db,
        cycle_id=cycle_id,
        export_format=format.lower(),
        actor=actor,
        request_id=request_id,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/edges/{edge_id}",
    response_model=ConflictEdgeDetailResponse,
    summary="Privileged drilldown: shared students for a specific conflict edge (P6.11)",
)
def get_edge_drilldown_by_id(
    cycle_id: str,
    edge_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ConflictEdgeDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    return graph_service.get_edge_shared_students(
        db=db,
        cycle_id=cycle_id,
        edge_id=edge_id,
        actor=actor,
        request_id=request_id,
    )


@router.get(
    "/edges",
    response_model=ConflictEdgeDetailResponse,
    summary="Privileged drilldown: shared students by exam pair (examA, examB) (P6.11)",
)
def get_edge_drilldown_by_pair(
    cycle_id: str,
    exam_a: str = Query(..., alias="examA"),
    exam_b: str = Query(..., alias="examB"),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    request: Request = None,  # type: ignore[assignment]
) -> ConflictEdgeDetailResponse:
    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None
    return graph_service.get_edge_shared_students(
        db=db,
        cycle_id=cycle_id,
        exam_a=exam_a,
        exam_b=exam_b,
        actor=actor,
        request_id=request_id,
    )
