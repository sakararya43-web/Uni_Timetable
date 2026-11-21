"""Pydantic Schemas for Schedule Generation, Validation, Comparison, and Versioning.

PRD §13, §14, §15, §17.13 - 17.15, §18.7, Tasks P8.1 - P8.21.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScheduleRunStatus, ScheduleStatus


class ScheduleGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    algorithm: str = Field(default="dsatur", description="dsatur, welsh_powell, or greedy")
    preserveLockedExams: bool = Field(default=True, alias="preserve_locked_exams")
    optimizeSoftConstraints: bool = Field(default=False, alias="optimize_soft_constraints")
    autoRebuildGraph: bool = Field(default=False, alias="auto_rebuild_graph")


class HardViolationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    examIds: list[str] = Field(default_factory=list, alias="exam_ids")
    slotId: str | None = Field(default=None, alias="slot_id")
    message: str
    sharedStudentCount: int = Field(default=0, alias="shared_student_count")


class SoftBreakdownSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rule: str
    weight: float
    count: int
    penalty: float
    message: str


class ScheduleValidationReportSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    hardViolations: list[HardViolationSchema] = Field(default_factory=list, alias="hard_violations")
    softPenaltyTotal: float = Field(default=0.0, alias="soft_penalty_total")
    softBreakdown: list[SoftBreakdownSchema] = Field(default_factory=list, alias="soft_breakdown")
    warnings: list[str] = Field(default_factory=list)


class ScheduleRunResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    graphSnapshotId: str = Field(alias="graph_snapshot_id")
    algorithm: str
    algorithmVersion: str = Field(alias="algorithm_version")
    executionTimeMs: float = Field(alias="execution_time_ms")
    colorsUsed: int = Field(alias="colors_used")
    isValid: bool = Field(alias="is_valid")
    softScore: float = Field(alias="soft_score")
    status: ScheduleRunStatus
    configJson: dict[str, Any] = Field(alias="config_json")
    resultSummaryJson: dict[str, Any] = Field(alias="result_summary_json")
    createdAt: datetime = Field(alias="created_at")


class AlgorithmComparisonItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    algorithm: str
    algorithmVersion: str = Field(alias="algorithm_version")
    status: str
    colorsUsed: int = Field(alias="colors_used")
    executionTimeMs: float = Field(alias="execution_time_ms")
    isValid: bool = Field(alias="is_valid")
    softScore: float = Field(alias="soft_score")
    examsScheduled: int = Field(alias="exams_scheduled")
    unscheduledCount: int = Field(alias="unscheduled_count")
    isFeasible: bool = Field(alias="is_feasible")
    notes: list[str] = Field(default_factory=list)


class ScheduleComparisonResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cycleId: str = Field(alias="cycle_id")
    graphSnapshotId: str = Field(alias="graph_snapshot_id")
    results: list[AlgorithmComparisonItem]
    notes: list[str] = Field(default_factory=list)


class ExamAssignmentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    scheduleVersionId: str = Field(alias="schedule_version_id")
    examId: str = Field(alias="exam_id")
    timeSlotId: str = Field(alias="time_slot_id")
    colorId: int = Field(alias="color_id")
    locked: bool
    manualOverride: bool = Field(alias="manual_override")
    subjectCode: str | None = Field(default=None, alias="subject_code")
    subjectName: str | None = Field(default=None, alias="subject_name")
    slotDate: date | None = Field(default=None, alias="slot_date")
    slotStartTime: str | None = Field(default=None, alias="slot_start_time")
    slotEndTime: str | None = Field(default=None, alias="slot_end_time")
    sessionLabel: str | None = Field(default=None, alias="session_label")


class ScheduleVersionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    versionNumber: int = Field(alias="version_number")
    scheduleRunId: str | None = Field(default=None, alias="schedule_run_id")
    status: ScheduleStatus
    publishedAt: datetime | None = Field(default=None, alias="published_at")
    softScore: float = Field(alias="soft_score")
    assignmentCount: int = Field(default=0, alias="assignment_count")
    validationReport: ScheduleValidationReportSchema | None = Field(
        default=None, alias="validation_report"
    )
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")
