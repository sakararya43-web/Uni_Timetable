"""Pydantic schemas for Publishing, Student Timetables, Master Timetables, Reports, and Audit Logs.

PRD §16, §18.7, §20, §21, §23, §26.5, Tasks P10.1 - P10.21.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AuditAction, ScheduleStatus


class PublishScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    confirm: bool = Field(default=True, description="Explicit confirmation to publish timetable")
    notes: str | None = Field(default=None, description="Optional release notes or remarks")


class StudentTimetableEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    departmentCode: str | None = Field(default=None, alias="department_code")
    examDate: date = Field(alias="exam_date")
    startTime: str = Field(alias="start_time")
    endTime: str = Field(alias="end_time")
    durationMinutes: int = Field(alias="duration_minutes")
    sessionLabel: str = Field(alias="session_label")


class StudentTimetableResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    studentId: str = Field(alias="student_id")
    studentNumber: str = Field(alias="student_number")
    studentName: str = Field(alias="student_name")
    cycleId: str = Field(alias="cycle_id")
    cycleName: str = Field(alias="cycle_name")
    scheduleVersionId: str = Field(alias="schedule_version_id")
    versionNumber: int = Field(alias="version_number")
    publishedAt: datetime | None = Field(default=None, alias="published_at")
    exams: list[StudentTimetableEntry] = Field(default_factory=list)


class MasterTimetableEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assignmentId: str = Field(alias="assignment_id")
    examId: str = Field(alias="exam_id")
    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    departmentCode: str | None = Field(default=None, alias="department_code")
    departmentName: str | None = Field(default=None, alias="department_name")
    slotDate: date = Field(alias="slot_date")
    startTime: str = Field(alias="start_time")
    endTime: str = Field(alias="end_time")
    durationMinutes: int = Field(alias="duration_minutes")
    sessionLabel: str = Field(alias="session_label")
    studentCount: int = Field(alias="student_count")
    locked: bool
    manualOverride: bool = Field(alias="manual_override")


class MasterTimetableResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scheduleVersionId: str = Field(alias="schedule_version_id")
    versionNumber: int = Field(alias="version_number")
    cycleId: str = Field(alias="cycle_id")
    cycleName: str = Field(alias="cycle_name")
    status: ScheduleStatus
    publishedAt: datetime | None = Field(default=None, alias="published_at")
    totalExams: int = Field(alias="total_exams")
    entries: list[MasterTimetableEntry] = Field(default_factory=list)


class CycleReportSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cycleId: str = Field(alias="cycle_id")
    cycleName: str = Field(alias="cycle_name")
    examStartDate: date = Field(alias="exam_start_date")
    examEndDate: date = Field(alias="exam_end_date")
    totalSubjects: int = Field(alias="total_subjects")
    totalExams: int = Field(alias="total_exams")
    totalStudents: int = Field(alias="total_students")
    totalEnrollments: int = Field(alias="total_enrollments")
    totalSlots: int = Field(alias="total_slots")
    slotsUsed: int = Field(alias="slots_used")
    graphVertices: int = Field(alias="graph_vertices")
    graphEdges: int = Field(alias="graph_edges")
    averageDegree: float = Field(alias="average_degree")
    latestPublishedVersion: int | None = Field(default=None, alias="latest_published_version")
    latestPublishedAt: datetime | None = Field(default=None, alias="latest_published_at")


class DateDistributionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: date
    examCount: int = Field(alias="exam_count")
    studentSessions: int = Field(alias="student_sessions")


class SessionDistributionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sessionLabel: str = Field(alias="session_label")
    examCount: int = Field(alias="exam_count")
    studentSessions: int = Field(alias="student_sessions")


class MultiExamStudentItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    examsPerDay: int = Field(alias="exams_per_day")
    studentCount: int = Field(alias="student_count")


class ScheduleDistributionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scheduleVersionId: str = Field(alias="schedule_version_id")
    versionNumber: int = Field(alias="version_number")
    byDate: list[DateDistributionItem] = Field(default_factory=list, alias="by_date")
    bySession: list[SessionDistributionItem] = Field(default_factory=list, alias="by_session")
    multiExamDays: list[MultiExamStudentItem] = Field(default_factory=list, alias="multi_exam_days")


class AuditLogListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    actorId: str | None = Field(default=None, alias="actor_id")
    actorEmail: str = Field(alias="actor_email")
    action: AuditAction
    entityType: str = Field(alias="entity_type")
    entityId: str | None = Field(default=None, alias="entity_id")
    beforeState: dict[str, Any] | None = Field(default=None, alias="before_state")
    afterState: dict[str, Any] | None = Field(default=None, alias="after_state")
    requestId: str | None = Field(default=None, alias="request_id")
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    items: list[AuditLogListItem] = Field(default_factory=list)
