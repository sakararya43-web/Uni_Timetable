"""Pydantic schemas for Schedule Versioning, Manual Editing, Locking, and Regeneration.

PRD §15, §17.14, §17.15, §18.7, Tasks P9.1 - P9.21.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScheduleStatus
from app.schemas.schedule import HardViolationSchema, ScheduleValidationReportSchema


class AssignmentDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    scheduleVersionId: str = Field(alias="schedule_version_id")
    examId: str = Field(alias="exam_id")
    timeSlotId: str = Field(alias="time_slot_id")
    colorId: int = Field(alias="color_id")
    locked: bool
    manualOverride: bool = Field(alias="manual_override")

    subjectId: str | None = Field(default=None, alias="subject_id")
    subjectCode: str | None = Field(default=None, alias="subject_code")
    subjectName: str | None = Field(default=None, alias="subject_name")
    departmentCode: str | None = Field(default=None, alias="department_code")
    durationMinutes: int | None = Field(default=None, alias="duration_minutes")

    slotDate: date | None = Field(default=None, alias="slot_date")
    slotStartTime: str | None = Field(default=None, alias="slot_start_time")
    slotEndTime: str | None = Field(default=None, alias="slot_end_time")
    slotDurationMinutes: int | None = Field(default=None, alias="slot_duration_minutes")
    slotIndex: int | None = Field(default=None, alias="slot_index")
    sessionLabel: str | None = Field(default=None, alias="session_label")


class ScheduleVersionListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    versionNumber: int = Field(alias="version_number")
    scheduleRunId: str | None = Field(default=None, alias="schedule_run_id")
    status: ScheduleStatus
    publishedAt: datetime | None = Field(default=None, alias="published_at")
    softScore: float = Field(alias="soft_score")
    rowVersion: int = Field(alias="row_version")
    assignmentCount: int = Field(default=0, alias="assignment_count")
    lockedCount: int = Field(default=0, alias="locked_count")
    overrideCount: int = Field(default=0, alias="override_count")
    isValid: bool = Field(default=True, alias="is_valid")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")


class ScheduleVersionDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    versionNumber: int = Field(alias="version_number")
    scheduleRunId: str | None = Field(default=None, alias="schedule_run_id")
    status: ScheduleStatus
    publishedAt: datetime | None = Field(default=None, alias="published_at")
    softScore: float = Field(alias="soft_score")
    rowVersion: int = Field(alias="row_version")
    assignments: list[AssignmentDetailResponse] = Field(default_factory=list)
    validationReport: ScheduleValidationReportSchema | None = Field(default=None, alias="validation_report")
    editHistory: list[dict[str, Any]] = Field(default_factory=list, alias="edit_history")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")


class PreviewMoveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    timeSlotId: str = Field(alias="time_slot_id")


class ConflictingExamItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    examId: str = Field(alias="exam_id")
    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    sharedStudentCount: int = Field(alias="shared_student_count")


class PreviewMoveResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    violations: list[HardViolationSchema] = Field(default_factory=list)
    conflictingExams: list[ConflictingExamItem] = Field(default_factory=list, alias="conflicting_exams")
    softPenaltyDelta: float = Field(default=0.0, alias="soft_penalty_delta")
    newSoftScore: float = Field(default=0.0, alias="new_soft_score")
    examLocked: bool = Field(default=False, alias="exam_locked")


class UpdateAssignmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    timeSlotId: str = Field(alias="time_slot_id")
    expectedRowVersion: int | None = Field(default=None, alias="expected_row_version")


class SwapAssignmentsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assignmentIdA: str = Field(alias="assignment_id_a")
    assignmentIdB: str = Field(alias="assignment_id_b")
    expectedRowVersion: int | None = Field(default=None, alias="expected_row_version")


class BulkLockRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    action: str = Field(description="'lock' or 'unlock'")
    date: str | None = None
    sessionLabel: str | None = Field(default=None, alias="session_label")
    examIds: list[str] | None = Field(default=None, alias="exam_ids")


class LockValidationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    conflicts: list[str] = Field(default_factory=list)
    lockedCount: int = Field(default=0, alias="locked_count")


class ScheduleRegenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    algorithm: str = Field(default="dsatur", description="dsatur, welsh_powell, or greedy")
    preserveLockedExams: bool = Field(default=True, alias="preserve_locked_exams")
    minimizeDisruption: bool = Field(default=True, alias="minimize_disruption")
    autoRebuildGraph: bool = Field(default=False, alias="auto_rebuild_graph")


class MovedExamItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    examId: str = Field(alias="exam_id")
    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    fromSlotId: str = Field(alias="from_slot_id")
    fromSlotDate: str = Field(alias="from_slot_date")
    fromSlotSession: str = Field(alias="from_slot_session")
    toSlotId: str = Field(alias="to_slot_id")
    toSlotDate: str = Field(alias="to_slot_date")
    toSlotSession: str = Field(alias="to_slot_session")


class ChangeImpactReportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    oldVersionId: str = Field(alias="old_version_id")
    newVersionId: str = Field(alias="new_version_id")
    examsMovedCount: int = Field(alias="exams_moved_count")
    examsUnchangedCount: int = Field(alias="exams_unchanged_count")
    lockedPreservedCount: int = Field(alias="locked_preserved_count")
    oldSoftScore: float = Field(alias="old_soft_score")
    newSoftScore: float = Field(alias="new_soft_score")
    softScoreDelta: float = Field(alias="soft_score_delta")
    oldHardValid: bool = Field(alias="old_hard_valid")
    newHardValid: bool = Field(alias="new_hard_valid")
    movedExams: list[MovedExamItem] = Field(default_factory=list, alias="moved_exams")
    newExamsAdded: list[str] = Field(default_factory=list, alias="new_exams_added")
    examsRemoved: list[str] = Field(default_factory=list, alias="exams_removed")
