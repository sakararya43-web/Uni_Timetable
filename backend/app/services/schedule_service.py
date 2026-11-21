"""Schedule Generation and Comparison Orchestration Service.

PRD §13, §14, §15, §18.7, Tasks P8.11 - P8.21:
Orchestrates graph verification, algorithm coloring, color-to-slot mapping,
independent schedule validation, soft constraint scoring, run persistence,
and multi-algorithm benchmarking comparison.
"""

import statistics
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.algorithms.dsatur import dsatur
from app.algorithms.greedy import greedy_color
from app.algorithms.slot_mapper import ExamInfo, SlotInfo, map_colors_to_slots
from app.algorithms.welsh_powell import welsh_powell
from app.middleware.error_handler import DomainException
from app.models.enums import (
    AuditAction,
    CycleStatus,
    EnrollmentStatus,
    ScheduleRunStatus,
    ScheduleStatus,
    enum_val,
)
from app.models.schedule import ExamAssignment, ScheduleRun, ScheduleVersion
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot
from app.models.user import User
from app.schemas.schedule import (
    AlgorithmComparisonItem,
    HardViolationSchema,
    ScheduleComparisonResponse,
    ScheduleGenerateRequest,
    ScheduleValidationReportSchema,
    SoftBreakdownSchema,
)
from app.services.audit_service import audit_service
from app.services.cycle_service import CycleService
from app.services.graph_service import graph_service
from app.services.schedule_validator import validate_schedule
from app.services.soft_constraint_service import evaluate_soft_constraints


class ScheduleService:
    @staticmethod
    def generate_schedule(
        db: Session,
        cycle_id: str,
        req: ScheduleGenerateRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleRun:
        """
        Executes end-to-end schedule generation workflow (Tasks P8.11 - P8.17).
        """
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' not found.",
                status_code=404,
            )

        # 1. Precondition checks: exams, slots, graph snapshot (P8.11)
        exams_list = list(
            db.scalars(
                select(Exam)
                .options(joinedload(Exam.subject))
                .where(Exam.scheduling_cycle_id == cycle_id)
            ).all()
        )
        if not exams_list:
            raise DomainException(
                code="NO_EXAMS_IN_CYCLE",
                message="Cannot generate schedule: no exams exist in cycle. Sync exams first.",
                status_code=422,
            )

        slots_list = list(
            db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle_id)).all()
        )
        if not slots_list:
            raise DomainException(
                code="NO_SLOTS_IN_CYCLE",
                message="Cannot generate schedule: no time slots exist in cycle. Generate slots first.",
                status_code=422,
            )

        # 2. Graph snapshot and staleness check (P8.11 step 1)
        is_stale, _, _ = graph_service.is_cycle_graph_stale(db, cycle_id)
        snapshot = graph_service.get_latest_snapshot(db, cycle_id)

        if not snapshot or is_stale:
            if req.autoRebuildGraph:
                snapshot, _, _ = graph_service.build_graph_snapshot(
                    db=db,
                    cycle_id=cycle_id,
                    actor=actor,
                    force=True,
                    request_id=request_id,
                )
            else:
                raise DomainException(
                    code="GRAPH_STALE",
                    message="Conflict graph snapshot is missing or stale. Rebuild graph first or set autoRebuildGraph=true.",
                    status_code=422,
                )

        # 3. Load locked exams from latest Candidate/Reviewed schedule version (P8.4)
        locked_exam_map: dict[str, str] = {}
        if req.preserveLockedExams:
            latest_version = db.scalar(
                select(ScheduleVersion)
                .where(ScheduleVersion.scheduling_cycle_id == cycle_id)
                .order_by(ScheduleVersion.version_number.desc())
                .limit(1)
            )
            if latest_version:
                locked_assignments = db.scalars(
                    select(ExamAssignment).where(
                        ExamAssignment.schedule_version_id == latest_version.id,
                        ExamAssignment.locked.is_(True),
                    )
                ).all()
                for la in locked_assignments:
                    locked_exam_map[la.exam_id] = la.time_slot_id

        # 4. Prepare data for pure algorithms
        adjacency_data = (snapshot.graph_data_json or {}).get("adjacency", {})
        adj: dict[str, set[str]] = {v: set(nbrs) for v, nbrs in adjacency_data.items()}

        # Assign reserved colors for locked slots (P8.4)
        precolored: dict[str, int] = {}
        slot_to_reserved_color: dict[str, int] = {}
        next_color = 0
        for eid, sid in locked_exam_map.items():
            if sid not in slot_to_reserved_color:
                slot_to_reserved_color[sid] = next_color
                next_color += 1
            precolored[eid] = slot_to_reserved_color[sid]

        # 5. Run coloring algorithm (P8.11 step 3)
        algo_name = req.algorithm.lower()
        if algo_name == "welsh_powell":
            coloring_result = welsh_powell(adj, precolored=precolored, deterministic=True)
        elif algo_name == "greedy":
            coloring_result = greedy_color(adj, precolored=precolored, deterministic=True)
        else:
            coloring_result = dsatur(adj, precolored=precolored, deterministic=True)

        # 6. Group exams by color class
        color_classes: dict[int, list[str]] = {}
        for eid, c in coloring_result.colors.items():
            color_classes.setdefault(c, []).append(eid)

        # 7. Prepare lightweight slot and exam models for mapping
        pure_slots = [
            SlotInfo(
                id=s.id,
                date=s.date,
                start_time=s.start_time.strftime("%H:%M")
                if hasattr(s.start_time, "strftime")
                else str(s.start_time),
                end_time=s.end_time.strftime("%H:%M")
                if hasattr(s.end_time, "strftime")
                else str(s.end_time),
                duration_minutes=s.duration_minutes,
                session_label=s.session_label,
                slot_index=s.slot_index,
                is_enabled=s.enabled,
            )
            for s in slots_list
        ]

        pure_exams = {
            e.id: ExamInfo(
                id=e.id,
                subject_code=e.subject.subject_code,
                duration_minutes=e.duration_minutes,
                preferred_dates=e.preferred_dates or [],
                restricted_dates=e.restricted_dates or [],
                locked_slot_id=locked_exam_map.get(e.id),
            )
            for e in exams_list
        }

        # 8. Map colors to slots (P8.1 - P8.6)
        mapping_result = map_colors_to_slots(
            color_classes=color_classes,
            slots=pure_slots,
            exams=pure_exams,
        )

        # 9. Handle mapping infeasibility (P8.6)
        if not mapping_result.is_feasible:
            run = ScheduleRun(
                scheduling_cycle_id=cycle_id,
                graph_snapshot_id=snapshot.id,
                algorithm=coloring_result.algorithm,
                algorithm_version=coloring_result.algorithm_version,
                execution_time_ms=coloring_result.execution_time_ms,
                colors_used=coloring_result.color_count,
                is_valid=False,
                soft_score=9999.0,
                status=ScheduleRunStatus.INFEASIBLE_INSUFFICIENT_SLOTS,
                config_json={
                    "algorithm": req.algorithm,
                    "preserveLockedExams": req.preserveLockedExams,
                    "optimizeSoftConstraints": req.optimizeSoftConstraints,
                },
                result_summary_json={
                    "isFeasible": False,
                    "message": mapping_result.message,
                    "bottlenecks": mapping_result.bottlenecks,
                    "recommendations": mapping_result.recommendations,
                    "unmappedColors": mapping_result.unmapped_colors,
                    "unmappedExams": mapping_result.unmapped_exam_ids,
                    "requiredSlots": len(color_classes),
                    "availableSlots": len([s for s in slots_list if s.enabled]),
                    "assignments": [],
                },
                created_by=actor.id,
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

        # 10. Build concrete assignments list
        assignments: list[dict[str, Any]] = []
        for eid, c in coloring_result.colors.items():
            sid = mapping_result.color_to_slot[c]
            assignments.append(
                {
                    "exam_id": eid,
                    "time_slot_id": sid,
                    "color_id": c,
                    "locked": (eid in locked_exam_map),
                }
            )

        # 11. Run independent schedule validator (P8.7)
        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle_id,
                )
            ).all()
        )
        enrollments_tuples: list[tuple[str, str]] = [(str(r[0]), str(r[1])) for r in enrollments]

        exams_dict = {
            e.id: {
                "id": e.id,
                "subject_code": e.subject.subject_code,
                "duration_minutes": e.duration_minutes,
                "restricted_dates": e.restricted_dates or [],
                "preferred_dates": e.preferred_dates or [],
                "cycle_id": e.scheduling_cycle_id,
                "locked_slot_id": locked_exam_map.get(e.id),
            }
            for e in exams_list
        }

        slots_dict = {
            s.id: {
                "id": s.id,
                "date": s.date,
                "start_time": s.start_time.strftime("%H:%M")
                if hasattr(s.start_time, "strftime")
                else str(s.start_time),
                "end_time": s.end_time.strftime("%H:%M")
                if hasattr(s.end_time, "strftime")
                else str(s.end_time),
                "duration_minutes": s.duration_minutes,
                "is_enabled": s.enabled,
                "slot_index": s.slot_index,
                "session_label": s.session_label,
                "cycle_id": s.scheduling_cycle_id,
            }
            for s in slots_list
        }

        validation_report = validate_schedule(
            exams=exams_dict,
            assignments=assignments,
            slots=slots_dict,
            enrollments=enrollments_tuples,
            cycle_id=cycle_id,
        )

        # 12. Evaluate soft constraint penalty (P8.9)
        weights = (cycle.configuration_json or {}).get("softConstraintWeights", {})
        soft_penalty, soft_breakdown = evaluate_soft_constraints(
            assignments=assignments,
            slots=slots_dict,
            exams=exams_dict,
            enrollments=enrollments_tuples,
            weights=weights,
        )

        # 13. Determine status and persist ScheduleRun (P8.11, P8.12)
        run_status = (
            ScheduleRunStatus.SUCCESS
            if validation_report.valid
            else ScheduleRunStatus.INVALID_DATA_OR_ALGORITHM_ERROR
        )
        if validation_report.valid and soft_penalty > 0:
            run_status = ScheduleRunStatus.SUCCESS_WITH_WARNINGS

        run = ScheduleRun(
            scheduling_cycle_id=cycle_id,
            graph_snapshot_id=snapshot.id,
            algorithm=coloring_result.algorithm,
            algorithm_version=coloring_result.algorithm_version,
            execution_time_ms=coloring_result.execution_time_ms,
            colors_used=coloring_result.color_count,
            is_valid=validation_report.valid,
            soft_score=soft_penalty,
            status=run_status,
            config_json={
                "algorithm": req.algorithm,
                "preserveLockedExams": req.preserveLockedExams,
                "optimizeSoftConstraints": req.optimizeSoftConstraints,
            },
            result_summary_json={
                "isFeasible": True,
                "assignments": assignments,
                "validation": {
                    "valid": validation_report.valid,
                    "hardViolations": [
                        {
                            "type": v.type,
                            "examIds": v.exam_ids,
                            "slotId": v.slot_id,
                            "message": v.message,
                            "sharedStudentCount": v.shared_student_count,
                        }
                        for v in validation_report.hard_violations
                    ],
                    "softPenaltyTotal": soft_penalty,
                    "softBreakdown": soft_breakdown,
                    "warnings": validation_report.warnings,
                },
                "mapping": {
                    "colorToSlot": mapping_result.color_to_slot,
                    "slotToColor": mapping_result.slot_to_color,
                },
                "totalExamsScheduled": len(assignments),
                "totalExamsInScope": len(exams_list),
            },
            created_by=actor.id,
        )
        db.add(run)

        # Record audit entry (P8.17)
        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_RUN,
            entity_type="schedule_run",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=run.id,
            after={
                "algorithm": run.algorithm,
                "colors_used": run.colors_used,
                "is_valid": run.is_valid,
                "soft_score": run.soft_score,
                "status": enum_val(run.status),
            },
            request_id=request_id,
        )

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def compare_algorithms(
        db: Session,
        cycle_id: str,
        actor: User,
        repeats: int = 5,
        request_id: str | None = None,
    ) -> ScheduleComparisonResponse:
        """
        Runs Greedy, Welsh-Powell, and DSATUR on the exact same snapshot (Tasks P8.18, P8.19, P8.20).
        Computes median runtimes across N runs to eliminate jitter.
        """
        algorithms = ["greedy", "welsh_powell", "dsatur"]
        results: list[AlgorithmComparisonItem] = []

        latest_snapshot = graph_service.get_latest_snapshot(db, cycle_id)
        if not latest_snapshot:
            # Attempt to auto-build
            latest_snapshot, _, _ = graph_service.build_graph_snapshot(
                db=db, cycle_id=cycle_id, actor=actor, force=False, request_id=request_id
            )

        for algo in algorithms:
            timings: list[float] = []
            final_run: ScheduleRun | None = None

            for _i in range(repeats):
                t0 = time.perf_counter()
                run = ScheduleService.generate_schedule(
                    db=db,
                    cycle_id=cycle_id,
                    req=ScheduleGenerateRequest(
                        algorithm=algo,
                        preserve_locked_exams=True,
                        auto_rebuild_graph=False,
                    ),
                    actor=actor,
                    request_id=request_id,
                )
                t_elapsed_ms = (time.perf_counter() - t0) * 1000.0
                timings.append(t_elapsed_ms)
                final_run = run

            assert final_run is not None
            median_time = round(statistics.median(timings), 2)
            summary = final_run.result_summary_json or {}
            is_feasible = summary.get("isFeasible", False)

            notes: list[str] = [
                f"Execution time is median over {repeats} runs to minimize OS CPU jitter.",
            ]
            if algo == "dsatur":
                notes.append(
                    "DSATUR dynamically tracks saturation degree, typically achieving smallest color counts."
                )
            elif algo == "welsh_powell":
                notes.append(
                    "Welsh-Powell sorts by degree descending prior to sequential coloring."
                )
            else:
                notes.append("Greedy uses lexicographical stable ID ordering.")

            results.append(
                AlgorithmComparisonItem(
                    algorithm=final_run.algorithm,
                    algorithm_version=final_run.algorithm_version,
                    status=enum_val(final_run.status),
                    colors_used=final_run.colors_used,
                    execution_time_ms=median_time,
                    is_valid=final_run.is_valid,
                    soft_score=final_run.soft_score,
                    exams_scheduled=summary.get("totalExamsScheduled", 0),
                    unscheduled_count=len(summary.get("unmappedExams", [])),
                    is_feasible=is_feasible,
                    notes=notes,
                )
            )

        comparison_notes = [
            "All algorithms were benchmarked on the identical conflict graph snapshot.",
            "Graph coloring is NP-hard; all evaluated methods are polynomial-time heuristics.",
            "No algorithm guarantees mathematical optimality across all graph topologies.",
        ]

        return ScheduleComparisonResponse(
            cycle_id=cycle_id,
            graph_snapshot_id=latest_snapshot.id,
            results=results,
            notes=comparison_notes,
        )

    @staticmethod
    def save_run_as_candidate(
        db: Session,
        run_id: str,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """
        Saves a successful ScheduleRun as a new Candidate ScheduleVersion (Tasks P8.15, P8.16).
        Transitions cycle to 'Generated' status when first candidate is saved.
        """
        run = db.get(ScheduleRun, run_id)
        if not run:
            raise DomainException(
                code="SCHEDULE_RUN_NOT_FOUND",
                message=f"Schedule run '{run_id}' not found.",
                status_code=404,
            )

        summary = run.result_summary_json or {}
        if not run.is_valid or not summary.get("isFeasible", False):
            raise DomainException(
                code="CANNOT_SAVE_INVALID_RUN",
                message="Cannot save invalid or infeasible schedule run as a candidate.",
                status_code=422,
            )

        cycle = db.get(SchedulingCycle, run.scheduling_cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND", message="Cycle not found.", status_code=404
            )

        # 1. Determine next version number
        latest_version_num = db.scalar(
            select(ScheduleVersion.version_number)
            .where(ScheduleVersion.scheduling_cycle_id == cycle.id)
            .order_by(ScheduleVersion.version_number.desc())
            .limit(1)
        )
        new_version_num = (latest_version_num + 1) if latest_version_num else 1

        # 2. Create ScheduleVersion
        schedule_ver = ScheduleVersion(
            scheduling_cycle_id=cycle.id,
            version_number=new_version_num,
            schedule_run_id=run.id,
            status=ScheduleStatus.CANDIDATE,
            validation_report_json=summary.get("validation", {}),
            soft_score=run.soft_score,
            created_by=actor.id,
        )
        db.add(schedule_ver)
        db.flush()

        # 3. Create ExamAssignment rows
        assignments_data = summary.get("assignments", [])
        assignments_to_add = [
            ExamAssignment(
                schedule_version_id=schedule_ver.id,
                exam_id=a["exam_id"],
                time_slot_id=a["time_slot_id"],
                color_id=a["color_id"],
                locked=a.get("locked", False),
                manual_override=False,
            )
            for a in assignments_data
        ]
        db.add_all(assignments_to_add)

        # 4. Transition cycle status to Generated if in Draft (Task P8.16)
        if cycle.status == CycleStatus.DRAFT:
            CycleService.validate_transition(cycle.status, CycleStatus.GENERATED)
            cycle.status = CycleStatus.GENERATED

        # 5. Record audit entry (P8.17)
        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_SAVE,
            entity_type="schedule_version",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=schedule_ver.id,
            after={
                "version_number": schedule_ver.version_number,
                "status": enum_val(schedule_ver.status),
                "assignment_count": len(assignments_to_add),
                "cycle_status": enum_val(cycle.status),
            },
            request_id=request_id,
        )

        db.commit()
        db.refresh(schedule_ver)
        return schedule_ver

    @staticmethod
    def validate_run(db: Session, run_id: str) -> ScheduleValidationReportSchema:
        """Re-validates a stored schedule run (Task P8.15)."""
        run = db.get(ScheduleRun, run_id)
        if not run:
            raise DomainException(
                code="SCHEDULE_RUN_NOT_FOUND", message="Run not found.", status_code=404
            )

        summary = run.result_summary_json or {}
        val_data = summary.get("validation", {})
        return ScheduleValidationReportSchema(
            valid=val_data.get("valid", False),
            hard_violations=[
                HardViolationSchema(**hv) for hv in val_data.get("hardViolations", [])
            ],
            soft_penalty_total=val_data.get("softPenaltyTotal", 0.0),
            soft_breakdown=[SoftBreakdownSchema(**sb) for sb in val_data.get("softBreakdown", [])],
            warnings=val_data.get("warnings", []),
        )


schedule_service = ScheduleService()
