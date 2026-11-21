import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import EntityStatus

SUBJECT_CODE_REGEX = re.compile(r"^[A-Za-z0-9_-]{2,32}$")


class SubjectCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subjectCode: str = Field(min_length=2, max_length=32, alias="subject_code")
    subjectName: str = Field(min_length=2, max_length=255, alias="subject_name")
    departmentId: str = Field(alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int = Field(ge=1, le=16)
    credits: float = Field(default=3.0, ge=0.0)
    defaultDurationMinutes: int = Field(default=180, ge=30, le=360, alias="default_duration_minutes")
    priority: int = Field(default=1, ge=1, le=10)

    preferredDates: list[str] = Field(default_factory=list, alias="preferred_dates")
    restrictedDates: list[str] = Field(default_factory=list, alias="restricted_dates")

    @field_validator("subjectCode")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not SUBJECT_CODE_REGEX.match(v.strip()):
            raise ValueError("subject_code must be 2-32 alphanumeric characters, dashes, or underscores.")
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_date_overlap(self) -> "SubjectCreate":
        pref_set = set(self.preferredDates)
        rest_set = set(self.restrictedDates)
        overlap = pref_set.intersection(rest_set)
        if overlap:
            raise ValueError(f"Dates cannot appear in both preferred and restricted sets: {', '.join(sorted(overlap))}")
        return self


class SubjectUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subjectName: str | None = Field(default=None, min_length=2, max_length=255, alias="subject_name")
    departmentId: str | None = Field(default=None, alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int | None = Field(default=None, ge=1, le=16)
    credits: float | None = Field(default=None, ge=0.0)
    defaultDurationMinutes: int | None = Field(default=None, ge=30, le=360, alias="default_duration_minutes")
    priority: int | None = Field(default=None, ge=1, le=10)
    preferredDates: list[str] | None = Field(default=None, alias="preferred_dates")
    restrictedDates: list[str] | None = Field(default=None, alias="restricted_dates")
    status: EntityStatus | None = None

    @model_validator(mode="after")
    def validate_date_overlap(self) -> "SubjectUpdate":
        if self.preferredDates is not None and self.restrictedDates is not None:
            pref_set = set(self.preferredDates)
            rest_set = set(self.restrictedDates)
            overlap = pref_set.intersection(rest_set)
            if overlap:
                raise ValueError(f"Dates cannot appear in both preferred and restricted sets: {', '.join(sorted(overlap))}")
        return self


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    departmentId: str = Field(alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int
    credits: float
    defaultDurationMinutes: int = Field(alias="default_duration_minutes")
    priority: int
    preferredDates: list[str] = Field(default_factory=list, alias="preferred_dates")
    restrictedDates: list[str] = Field(default_factory=list, alias="restricted_dates")
    status: EntityStatus

    # Derived fields dynamically calculated via query (FR-03, Task P3.5, P3.7)
    enrollmentCount: int = Field(default=0, alias="enrollment_count")
    conflictDegree: int | None = Field(default=None, alias="conflict_degree")
    schedulingStatus: str | None = Field(default=None, alias="scheduling_status")


class PaginatedSubjectsResponse(BaseModel):
    items: list[SubjectResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
