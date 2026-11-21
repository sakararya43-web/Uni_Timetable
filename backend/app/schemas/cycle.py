from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CycleStatus, EntityStatus


# ==============================================================================
# Configuration Sub-Schemas (Task P5.2, PRD §FR-06, §14.3)
# ==============================================================================
class SessionConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str = Field(min_length=1, max_length=64)  # e.g. "Morning", "Afternoon"
    startTime: str = Field(alias="start_time")  # "HH:MM" e.g. "09:00"
    endTime: str = Field(alias="end_time")  # "HH:MM" e.g. "12:00"
    enabled: bool = True
    durationMinutes: int | None = Field(default=None, alias="duration_minutes")

    @model_validator(mode="after")
    def validate_times(self) -> "SessionConfig":
        try:
            sh, sm = map(int, self.startTime.split(":"))
            eh, em = map(int, self.endTime.split(":"))
            s_min = sh * 60 + sm
            e_min = eh * 60 + em
            if e_min <= s_min:
                raise ValueError(
                    f"Session '{self.label}': end_time ({self.endTime}) must be strictly after start_time ({self.startTime})."
                )
            if self.durationMinutes is None:
                self.durationMinutes = e_min - s_min
        except Exception as exc:
            if isinstance(exc, ValueError) and "strictly after" in str(exc):
                raise
            raise ValueError(
                f"Invalid time format in session '{self.label}'. Expected HH:MM."
            ) from exc
        return self


class BreakConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    startTime: str = Field(alias="start_time")
    endTime: str = Field(alias="end_time")


class HolidayConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str  # "YYYY-MM-DD"
    label: str | None = None


class SpecialRestrictionConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str  # "YYYY-MM-DD"
    sessionLabel: str | None = Field(default=None, alias="session_label")
    enabled: bool = False
    reason: str | None = None


class SoftConstraintWeights(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    twoExamsInOneDay: int = Field(default=10, alias="two_exams_in_one_day")
    consecutiveSessions: int = Field(default=5, alias="consecutive_sessions")
    sessionLoadExceeded: int = Field(default=3, alias="session_load_exceeded")
    preferredDateMissed: int = Field(default=2, alias="preferred_date_missed")
    unlockedExamMoved: int = Field(default=1, alias="unlocked_exam_moved")


class CycleScopeConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    departmentIds: list[str] | None = Field(default=None, alias="department_ids")
    programIds: list[str] | None = Field(default=None, alias="program_ids")
    semesterNumbers: list[int] | None = Field(default=None, alias="semester_numbers")


class CycleConfiguration(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schemaVersion: int = Field(default=1, alias="schema_version")
    startDate: date = Field(alias="start_date")
    endDate: date = Field(alias="end_date")
    timezone: str = "UTC"
    examDaysOfWeek: list[int] = Field(
        default=[1, 2, 3, 4, 5, 6], alias="exam_days_of_week"
    )  # ISO 1=Monday..7=Sunday
    holidays: list[str | HolidayConfig] = Field(default_factory=list)
    sessions: list[SessionConfig] = Field(default_factory=list)
    breaks: list[BreakConfig] = Field(default_factory=list)
    maxExamsPerSession: int | None = Field(default=None, alias="max_exams_per_session")
    maxExamsPerDay: int | None = Field(default=None, alias="max_exams_per_day")
    allowedDurations: list[int] = Field(default=[180], alias="allowed_durations")
    defaultDurationMinutes: int = Field(default=180, alias="default_duration_minutes")
    preferredTimeSlots: list[dict[str, Any]] = Field(
        default_factory=list, alias="preferred_time_slots"
    )
    specialRestrictions: list[SpecialRestrictionConfig] = Field(
        default_factory=list, alias="special_restrictions"
    )
    softConstraintWeights: SoftConstraintWeights = Field(
        default_factory=SoftConstraintWeights, alias="soft_constraint_weights"
    )
    scope: CycleScopeConfig = Field(default_factory=CycleScopeConfig)

    @model_validator(mode="after")
    def validate_cycle_config(self) -> "CycleConfiguration":
        # 1. Date range
        if self.endDate < self.startDate:
            raise ValueError("end_date cannot be earlier than start_date.")

        # 2. Weekdays
        if not self.examDaysOfWeek:
            raise ValueError("exam_days_of_week must contain at least one day (1=Mon..7=Sun).")
        for d in self.examDaysOfWeek:
            if d < 1 or d > 7:
                raise ValueError(f"Invalid weekday {d}. Allowed values: 1 (Mon) through 7 (Sun).")

        # 3. Non-overlapping sessions
        if len(self.sessions) > 1:
            sorted_sessions = sorted(self.sessions, key=lambda s: s.startTime)
            for i in range(len(sorted_sessions) - 1):
                cur = sorted_sessions[i]
                nxt = sorted_sessions[i + 1]
                if nxt.startTime < cur.endTime:
                    raise ValueError(
                        f"Overlapping sessions detected: '{cur.label}' ({cur.startTime}-{cur.endTime}) "
                        f"overlaps with '{nxt.label}' ({nxt.startTime}-{nxt.endTime})."
                    )

        # 4. Default duration in allowed durations
        if self.allowedDurations and self.defaultDurationMinutes not in self.allowedDurations:
            raise ValueError(
                f"default_duration_minutes ({self.defaultDurationMinutes}) must be in allowed_durations {self.allowedDurations}."
            )

        return self


# ==============================================================================
# Cycle CRUD Schemas (Task P5.1)
# ==============================================================================
class CycleCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=2, max_length=255)
    academicYearId: str = Field(alias="academic_year_id")
    semesterId: str | None = Field(default=None, alias="semester_id")
    startDate: date = Field(alias="start_date")
    endDate: date = Field(alias="end_date")
    timezone: str = "UTC"
    configuration: CycleConfiguration | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CycleCreate":
        if self.endDate < self.startDate:
            raise ValueError("end_date cannot be earlier than start_date.")
        return self


class CycleUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    startDate: date | None = Field(default=None, alias="start_date")
    endDate: date | None = Field(default=None, alias="end_date")
    timezone: str | None = None
    status: CycleStatus | None = None
    configuration: CycleConfiguration | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CycleUpdate":
        if (
            self.startDate is not None
            and self.endDate is not None
            and self.endDate < self.startDate
        ):
            raise ValueError("end_date cannot be earlier than start_date.")
        return self


class CycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    academicYearId: str = Field(alias="academic_year_id")
    semesterId: str | None = Field(default=None, alias="semester_id")
    startDate: date = Field(alias="start_date")
    endDate: date = Field(alias="end_date")
    timezone: str
    status: CycleStatus
    dataVersion: int = Field(alias="data_version")
    configurationJson: dict[str, Any] = Field(alias="configuration_json")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")


class PaginatedCyclesResponse(BaseModel):
    items: list[CycleResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


# ==============================================================================
# TimeSlot Schemas (Task P5.8, P5.10, P5.11)
# ==============================================================================
class TimeSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    date: date
    startTime: str = Field(alias="start_time")
    endTime: str = Field(alias="end_time")
    durationMinutes: int = Field(alias="duration_minutes")
    sessionLabel: str = Field(alias="session_label")
    slotIndex: int = Field(alias="slot_index")
    enabled: bool
    capacity: int | None = None


class PaginatedSlotsResponse(BaseModel):
    items: list[TimeSlotResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


class CapacitySummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cycleId: str = Field(alias="cycle_id")
    totalSlots: int = Field(alias="total_slots")
    enabledSlots: int = Field(alias="enabled_slots")
    disabledSlots: int = Field(alias="disabled_slots")
    slotsByDurationBucket: dict[int, int] = Field(alias="slots_by_duration_bucket")
    slotsByDay: list[dict[str, Any]] = Field(alias="slots_by_day")
    examCount: int = Field(alias="exam_count")
    durationIncompatibleExamsCount: int = Field(alias="duration_incompatible_exams_count")
    isFeasiblePreCheck: bool = Field(alias="is_feasible_pre_check")
    warnings: list[str] = Field(default_factory=list)


# ==============================================================================
# Exam Schemas (Task P5.4, P5.5)
# ==============================================================================
class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    schedulingCycleId: str = Field(alias="scheduling_cycle_id")
    subjectId: str = Field(alias="subject_id")
    subjectCode: str | None = Field(default=None, alias="subject_code")
    subjectName: str | None = Field(default=None, alias="subject_name")
    durationMinutes: int = Field(alias="duration_minutes")
    priority: int
    preferredDates: list[str] = Field(default_factory=list, alias="preferred_dates")
    restrictedDates: list[str] = Field(default_factory=list, alias="restricted_dates")
    status: EntityStatus


class ExamUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    durationMinutes: int | None = Field(default=None, ge=30, le=360, alias="duration_minutes")
    priority: int | None = Field(default=None, ge=1, le=10)
    preferredDates: list[str] | None = Field(default=None, alias="preferred_dates")
    restrictedDates: list[str] | None = Field(default=None, alias="restricted_dates")

    @model_validator(mode="after")
    def validate_date_overlap(self) -> "ExamUpdate":
        if self.preferredDates is not None and self.restrictedDates is not None:
            overlap = set(self.preferredDates).intersection(set(self.restrictedDates))
            if overlap:
                raise ValueError(
                    f"Dates cannot appear in both preferred and restricted: {', '.join(sorted(overlap))}"
                )
        return self


class ExamSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cycleId: str = Field(alias="cycle_id")
    syncedExamsCount: int = Field(alias="synced_exams_count")
    addedCount: int = Field(alias="added_count")
    removedCount: int = Field(alias="removed_count")
    message: str


class PaginatedExamsResponse(BaseModel):
    items: list[ExamResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
