"""Conflict Graph Service.

PRD §11 (FR-07), §18.6, §23, Tasks P6.7 - P6.14:
Handles graph snapshot persistence, idempotency, staleness detection,
exporting, and privileged conflict drilldown.
"""

import csv
import io
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.algorithms.graph_builder import (
    build_conflict_graph,
    compute_enrollment_hash,
    compute_stats,
    validate_graph,
)
from app.algorithms.types import GraphValidationReport
from app.middleware.error_handler import DomainException
from app.models.academic import Student, Subject
from app.models.enums import AuditAction, EnrollmentStatus
from app.models.graph import ConflictEdge, ConflictGraphSnapshot
from app.models.scheduling import Enrollment, Exam, SchedulingCycle
from app.models.user import User
from app.schemas.graph import (
    ConflictEdgeDetailResponse,
    ConflictGraphResponse,
    GraphEdge,
    GraphNode,
    GraphStatsResponse,
    SharedStudentInfo,
)
from app.services.audit_service import audit_service


class GraphService:
    @staticmethod
    def get_latest_snapshot(db: Session, cycle_id: str) -> ConflictGraphSnapshot | None:
        """Retrieves the most recent ConflictGraphSnapshot for a scheduling cycle."""
        return db.scalar(
            select(ConflictGraphSnapshot)
            .where(ConflictGraphSnapshot.scheduling_cycle_id == cycle_id)
            .order_by(ConflictGraphSnapshot.version.desc())
            .limit(1)
        )

    @staticmethod
    def is_cycle_graph_stale(db: Session, cycle_id: str) -> tuple[bool, str, str]:
        """
        Calculates whether the latest graph snapshot is stale (Task P6.10).
        Returns (is_stale, current_enrollment_hash, snapshot_enrollment_hash).
        """
        latest_snapshot = GraphService.get_latest_snapshot(db, cycle_id)

        # Query active in-scope exams and enrollments
        exam_ids = list(
            db.scalars(
                select(Exam.id).where(Exam.scheduling_cycle_id == cycle_id)
            ).all()
        )
        if not exam_ids:
            return (True, "", latest_snapshot.enrollment_snapshot_hash if latest_snapshot else "")

        # Map subject_id to exam_id
        exams = db.execute(
            select(Exam.id, Exam.subject_id).where(Exam.scheduling_cycle_id == cycle_id)
        ).all()
        sub_to_exam = {sub_id: e_id for e_id, sub_id in exams}

        enrollments = db.execute(
            select(Enrollment.student_id, Enrollment.subject_id).where(
                Enrollment.cycle_id == cycle_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        ).all()

        enr_pairs = [
            (s_id, sub_to_exam[sub_id])
            for s_id, sub_id in enrollments
            if sub_id in sub_to_exam
        ]

        current_hash = compute_enrollment_hash(exam_ids, enr_pairs)
        if not latest_snapshot:
            return (True, current_hash, "")

        is_stale = (latest_snapshot.enrollment_snapshot_hash != current_hash)
        return (is_stale, current_hash, latest_snapshot.enrollment_snapshot_hash)

    @staticmethod
    def build_graph_snapshot(
        db: Session,
        cycle_id: str,
        actor: User,
        force: bool = False,
        request_id: str | None = None,
    ) -> tuple[ConflictGraphSnapshot, bool, dict[str, Any]]:
        """
        Builds, validates, versions, and persists a conflict graph snapshot (Tasks P6.7, P6.8, P6.9).
        If the enrollment snapshot hash matches the latest snapshot and force is False,
        returns the existing snapshot as an idempotent no-op.
        """
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' not found.",
                status_code=404,
            )

        # 1. Efficient batch loading of in-scope exams with subject and department (P6.7)
        exams = list(
            db.scalars(
                select(Exam)
                .options(joinedload(Exam.subject).joinedload(Subject.department))
                .where(Exam.scheduling_cycle_id == cycle_id)
            ).all()
        )
        if not exams:
            raise DomainException(
                code="NO_EXAMS_IN_CYCLE",
                message="Cannot build conflict graph: no exams synchronized for this cycle. Run exam sync first.",
                status_code=422,
            )

        subject_to_exam = {exam.subject_id: exam.id for exam in exams}
        exam_ids = [exam.id for exam in exams]

        # 2. Efficient batch loading of active enrollments
        enrollments = list(
            db.scalars(
                select(Enrollment).where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            ).all()
        )

        enrollment_pairs: list[tuple[str, str]] = []
        for enr in enrollments:
            if enr.subject_id in subject_to_exam:
                enrollment_pairs.append((enr.student_id, subject_to_exam[enr.subject_id]))

        # 3. Canonical cryptographic enrollment hashing (P6.6)
        current_hash = compute_enrollment_hash(exam_ids, enrollment_pairs)

        # 4. Idempotency check (P6.9)
        latest_snapshot = GraphService.get_latest_snapshot(db, cycle_id)
        if latest_snapshot and latest_snapshot.enrollment_snapshot_hash == current_hash and not force:
            return (
                latest_snapshot,
                False,
                {"isValid": True, "errors": [], "warnings": ["Idempotent build: snapshot hash unchanged."]},
            )

        # 5. Build pure graph G = (V, E)
        vertex_metadata: dict[str, dict[str, Any]] = {}
        enrollment_counts: dict[str, int] = {}
        for _s_id, e_id in enrollment_pairs:
            enrollment_counts[e_id] = enrollment_counts.get(e_id, 0) + 1

        for exam in exams:
            vertex_metadata[exam.id] = {
                "subject_id": exam.subject_id,
                "subject_code": exam.subject.subject_code,
                "subject_name": exam.subject.subject_name,
                "department_id": exam.subject.department_id,
                "department_code": exam.subject.department.code if exam.subject.department else "",
                "semester": exam.subject.semester,
                "duration_minutes": exam.duration_minutes,
                "priority": exam.priority,
                "enrollment_count": enrollment_counts.get(exam.id, 0),
            }

        graph = build_conflict_graph(
            exam_ids=exam_ids,
            enrollments=enrollment_pairs,
            vertex_metadata=vertex_metadata,
        )

        # 6. Run independent validator (P6.4)
        validation_report: GraphValidationReport = validate_graph(graph, exam_ids, enrollment_pairs)
        if not validation_report.is_valid:
            raise DomainException(
                code="GRAPH_VALIDATION_FAILED",
                message=f"Conflict graph validation failed: {'; '.join(validation_report.errors)}",
                status_code=422,
            )

        # 7. Compute full statistics (P6.5)
        metrics = compute_stats(graph, enrollment_snapshot_hash=current_hash)

        # 8. Determine version number (P6.8)
        new_version = (latest_snapshot.version + 1) if latest_snapshot else 1

        top_exams = sorted(
            [
                {
                    "examId": v,
                    "degree": len(graph.adjacency.get(v, set())),
                    "subjectCode": vertex_metadata.get(v, {}).get("subject_code", ""),
                    "subjectName": vertex_metadata.get(v, {}).get("subject_name", ""),
                }
                for v in graph.vertices
            ],
            key=lambda item: (item["degree"], item["subjectCode"]),
            reverse=True,
        )[:10]

        graph_data_json = {
            "adjacency": {v: sorted(nbrs) for v, nbrs in graph.adjacency.items()},
            "edgeWeights": {f"{u}:{v}": w for (u, v), w in graph.edge_weights.items()},
            "stats": {
                "vertexCount": metrics.vertex_count,
                "edgeCount": metrics.edge_count,
                "density": metrics.density,
                "avgDegree": metrics.avg_degree,
                "maxDegree": metrics.max_degree,
                "minDegree": metrics.min_degree,
                "isolatedVertices": metrics.isolated_vertices,
                "isolatedCount": len(metrics.isolated_vertices),
                "connectedComponentsCount": metrics.connected_components_count,
                "largestComponentSize": metrics.largest_component_size,
                "degreeHistogram": {str(k): v for k, v in metrics.degree_histogram.items()},
                "chromaticLowerBound": metrics.chromatic_lower_bound,
                "topExamsByDegree": top_exams,
            },
            "vertexMetadata": vertex_metadata,
        }

        # 9. Persist snapshot row
        snapshot = ConflictGraphSnapshot(
            scheduling_cycle_id=cycle_id,
            version=new_version,
            vertex_count=metrics.vertex_count,
            edge_count=metrics.edge_count,
            density=metrics.density,
            avg_degree=metrics.avg_degree,
            max_degree=metrics.max_degree,
            chromatic_lower_bound=metrics.chromatic_lower_bound,
            enrollment_snapshot_hash=current_hash,
            graph_data_json=graph_data_json,
        )
        db.add(snapshot)
        db.flush()

        # 10. Bulk insert normalized conflict edges
        edges_to_insert = [
            ConflictEdge(
                graph_snapshot_id=snapshot.id,
                exam_id_a=u,
                exam_id_b=v,
                shared_student_count=w,
            )
            for (u, v), w in sorted(graph.edge_weights.items())
        ]
        if edges_to_insert:
            db.add_all(edges_to_insert)
            db.flush()

        # 11. Record audit entry (P6.14)
        audit_service.record(
            db=db,
            action=AuditAction.GRAPH_BUILD,
            entity_type="conflict_graph_snapshot",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=snapshot.id,
            after={
                "version": snapshot.version,
                "vertex_count": snapshot.vertex_count,
                "edge_count": snapshot.edge_count,
                "density": snapshot.density,
                "chromatic_lower_bound": snapshot.chromatic_lower_bound,
                "enrollment_snapshot_hash": snapshot.enrollment_snapshot_hash,
            },
            request_id=request_id,
        )

        db.commit()
        db.refresh(snapshot)

        return (
            snapshot,
            True,
            {
                "isValid": True,
                "errors": [],
                "warnings": validation_report.warnings,
                "vertexCountChecked": validation_report.vertex_count_checked,
                "edgeCountChecked": validation_report.edge_count_checked,
            },
        )

    @staticmethod
    def get_graph_response(
        db: Session,
        cycle_id: str,
        department_id: str | None = None,
        semester: int | None = None,
        min_weight: int | None = None,
    ) -> ConflictGraphResponse:
        """
        Retrieves graph payload with nodes, edges, and statistics (PRD §18.6).
        Strictly excludes any student identities to preserve student privacy (§23).
        """
        snapshot = GraphService.get_latest_snapshot(db, cycle_id)
        if not snapshot:
            raise DomainException(
                code="GRAPH_NOT_FOUND",
                message=f"No conflict graph has been built for scheduling cycle '{cycle_id}'.",
                status_code=404,
            )

        is_stale, cur_hash, snap_hash = GraphService.is_cycle_graph_stale(db, cycle_id)

        graph_data = snapshot.graph_data_json or {}
        adjacency = graph_data.get("adjacency", {})
        meta_dict = graph_data.get("vertexMetadata", {})

        # Build node list with optional filters
        nodes: list[GraphNode] = []
        matching_exam_ids: set[str] = set()

        for exam_id, meta in meta_dict.items():
            if department_id and meta.get("department_id") != department_id:
                continue
            if semester is not None and meta.get("semester") != semester:
                continue

            matching_exam_ids.add(exam_id)
            nodes.append(
                GraphNode(
                    id=exam_id,
                    subject_id=meta.get("subject_id", ""),
                    subject_code=meta.get("subject_code", ""),
                    subject_name=meta.get("subject_name", ""),
                    department_id=meta.get("department_id", ""),
                    department_code=meta.get("department_code"),
                    semester=meta.get("semester", 1),
                    enrollment_count=meta.get("enrollment_count", 0),
                    degree=len(adjacency.get(exam_id, [])),
                )
            )

        # Build edge list from ConflictEdge records
        edge_query = select(ConflictEdge).where(ConflictEdge.graph_snapshot_id == snapshot.id)
        if min_weight is not None and min_weight > 1:
            edge_query = edge_query.where(ConflictEdge.shared_student_count >= min_weight)

        all_edges = db.scalars(edge_query).all()
        edges: list[GraphEdge] = []
        for e in all_edges:
            # If nodes are filtered, both endpoints must match filter
            if (department_id or semester is not None) and (
                e.exam_id_a not in matching_exam_ids or e.exam_id_b not in matching_exam_ids
            ):
                continue

            edges.append(
                GraphEdge(
                    id=e.id,
                    exam_id_a=e.exam_id_a,
                    exam_id_b=e.exam_id_b,
                    subject_code_a=meta_dict.get(e.exam_id_a, {}).get("subject_code", ""),
                    subject_code_b=meta_dict.get(e.exam_id_b, {}).get("subject_code", ""),
                    shared_student_count=e.shared_student_count,
                )
            )

        stats_dict = graph_data.get("stats", {})
        stats = GraphStatsResponse(
            vertex_count=snapshot.vertex_count,
            edge_count=snapshot.edge_count,
            density=snapshot.density,
            avg_degree=snapshot.avg_degree,
            max_degree=snapshot.max_degree,
            min_degree=stats_dict.get("minDegree", 0),
            isolated_vertices=stats_dict.get("isolatedVertices", []),
            isolated_count=stats_dict.get("isolatedCount", 0),
            connected_components_count=stats_dict.get("connectedComponentsCount", 1),
            largest_component_size=stats_dict.get("largestComponentSize", snapshot.vertex_count),
            degree_histogram=stats_dict.get("degreeHistogram", {}),
            chromatic_lower_bound=snapshot.chromatic_lower_bound,
            top_exams_by_degree=stats_dict.get("topExamsByDegree", []),
        )

        return ConflictGraphResponse(
            snapshot_id=snapshot.id,
            cycle_id=cycle_id,
            version=snapshot.version,
            is_stale=is_stale,
            current_enrollment_hash=cur_hash,
            snapshot_enrollment_hash=snap_hash,
            stats=stats,
            nodes=nodes,
            edges=edges,
        )

    @staticmethod
    def get_graph_stats(db: Session, cycle_id: str) -> GraphStatsResponse:
        """Retrieves summary graph metrics (Task P6.5)."""
        snapshot = GraphService.get_latest_snapshot(db, cycle_id)
        if not snapshot:
            raise DomainException(
                code="GRAPH_NOT_FOUND",
                message=f"No conflict graph found for scheduling cycle '{cycle_id}'.",
                status_code=404,
            )

        stats_dict = (snapshot.graph_data_json or {}).get("stats", {})
        return GraphStatsResponse(
            vertex_count=snapshot.vertex_count,
            edge_count=snapshot.edge_count,
            density=snapshot.density,
            avg_degree=snapshot.avg_degree,
            max_degree=snapshot.max_degree,
            min_degree=stats_dict.get("minDegree", 0),
            isolated_vertices=stats_dict.get("isolatedVertices", []),
            isolated_count=stats_dict.get("isolatedCount", 0),
            connected_components_count=stats_dict.get("connectedComponentsCount", 1),
            largest_component_size=stats_dict.get("largestComponentSize", snapshot.vertex_count),
            degree_histogram=stats_dict.get("degreeHistogram", {}),
            chromatic_lower_bound=snapshot.chromatic_lower_bound,
            top_exams_by_degree=stats_dict.get("topExamsByDegree", []),
        )

    @staticmethod
    def export_graph(
        db: Session,
        cycle_id: str,
        export_format: str,
        actor: User,
        request_id: str | None = None,
    ) -> tuple[str, str, str]:
        """
        Exports conflict graph in JSON or CSV format without student identities (PRD §18.6, Task P6.11).
        Returns (content_string, media_type, filename).
        """
        response_data = GraphService.get_graph_response(db, cycle_id)

        audit_service.record(
            db=db,
            action=AuditAction.EXPORT,
            entity_type="conflict_graph_export",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=cycle_id,
            after={"format": export_format, "snapshot_version": response_data.version},
            request_id=request_id,
        )
        db.commit()

        if export_format.lower() == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow([
                "exam_id_a",
                "exam_id_b",
                "subject_code_a",
                "subject_code_b",
                "shared_student_count",
            ])
            for edge in response_data.edges:
                writer.writerow([
                    edge.examIdA,
                    edge.examIdB,
                    edge.subjectCodeA,
                    edge.subjectCodeB,
                    edge.sharedStudentCount,
                ])
            return buffer.getvalue(), "text/csv", f"conflict_graph_{cycle_id}_v{response_data.version}.csv"

        # Default JSON format
        json_content = json.dumps(response_data.model_dump(mode="json", by_alias=True), indent=2)
        return json_content, "application/json", f"conflict_graph_{cycle_id}_v{response_data.version}.json"

    @staticmethod
    def get_edge_shared_students(
        db: Session,
        cycle_id: str,
        edge_id: str | None = None,
        exam_a: str | None = None,
        exam_b: str | None = None,
        actor: User | None = None,
        request_id: str | None = None,
    ) -> ConflictEdgeDetailResponse:
        """
        Privileged drilldown endpoint returning shared students for a specific conflict edge.
        Restricted to staff (Admin and Coordinator) only; access is strictly audited (FR-07, PRD §23).
        """
        snapshot = GraphService.get_latest_snapshot(db, cycle_id)
        if not snapshot:
            raise DomainException(
                code="GRAPH_NOT_FOUND",
                message=f"No conflict graph found for scheduling cycle '{cycle_id}'.",
                status_code=404,
            )

        edge: ConflictEdge | None = None
        if edge_id:
            edge = db.get(ConflictEdge, edge_id)
        elif exam_a and exam_b:
            u, v = sorted([exam_a, exam_b])
            edge = db.scalar(
                select(ConflictEdge).where(
                    ConflictEdge.graph_snapshot_id == snapshot.id,
                    ConflictEdge.exam_id_a == u,
                    ConflictEdge.exam_id_b == v,
                )
            )

        if not edge:
            raise DomainException(
                code="CONFLICT_EDGE_NOT_FOUND",
                message="Specified conflict edge was not found in the latest graph snapshot.",
                status_code=404,
            )

        exam_obj_a = db.get(Exam, edge.exam_id_a)
        exam_obj_b = db.get(Exam, edge.exam_id_b)
        if not exam_obj_a or not exam_obj_b:
            raise DomainException(
                code="EXAM_NOT_FOUND",
                message="One or both exams for this conflict edge were not found.",
                status_code=404,
            )

        # Find all students actively enrolled in BOTH subjects
        students_subquery = (
            select(Enrollment.student_id)
            .where(
                Enrollment.cycle_id == cycle_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.subject_id.in_([exam_obj_a.subject_id, exam_obj_b.subject_id]),
            )
            .group_by(Enrollment.student_id)
            .having(func.count(Enrollment.id) >= 2)
        )

        students = db.scalars(
            select(Student)
            .options(joinedload(Student.program))
            .where(Student.id.in_(students_subquery))
            .order_by(Student.student_number.asc())
        ).all()

        # Audit drilldown access
        if actor:
            audit_service.record(
                db=db,
                action=AuditAction.GRAPH_DRILLDOWN,
                entity_type="conflict_edge",
                actor_email=actor.email,
                actor_id=actor.id,
                entity_id=edge.id,
                after={
                    "cycle_id": cycle_id,
                    "exam_id_a": edge.exam_id_a,
                    "exam_id_b": edge.exam_id_b,
                    "shared_student_count": len(students),
                },
                request_id=request_id,
            )
            db.commit()

        shared_student_list = [
            SharedStudentInfo(
                student_id=s.id,
                student_number=s.student_number,
                full_name=s.full_name,
                email=s.email,
                program_name=s.program.name if s.program else None,
            )
            for s in students
        ]

        return ConflictEdgeDetailResponse(
            edge_id=edge.id,
            exam_id_a=edge.exam_id_a,
            exam_id_b=edge.exam_id_b,
            subject_code_a=exam_obj_a.subject.subject_code,
            subject_code_b=exam_obj_b.subject.subject_code,
            subject_name_a=exam_obj_a.subject.subject_name,
            subject_name_b=exam_obj_b.subject.subject_name,
            shared_student_count=edge.shared_student_count,
            students=shared_student_list,
        )


graph_service = GraphService()
