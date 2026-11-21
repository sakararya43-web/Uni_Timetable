from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    studentId: str = Field(alias="student_id")
    subjectId: str = Field(alias="subject_id")
    cycleId: str = Field(alias="cycle_id")


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    studentId: str = Field(alias="student_id")
    studentNumber: str | None = Field(default=None, alias="student_number")
    studentName: str | None = Field(default=None, alias="student_name")
    subjectId: str = Field(alias="subject_id")
    subjectCode: str | None = Field(default=None, alias="subject_code")
    subjectName: str | None = Field(default=None, alias="subject_name")
    cycleId: str = Field(alias="cycle_id")
    status: EnrollmentStatus


class PaginatedEnrollmentsResponse(BaseModel):
    items: list[EnrollmentResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


class EnrollmentValidationReport(BaseModel):
    """Integrity diagnostic report returned by GET /enrollments/validate (Task P3.15)."""
    isValid: bool = Field(alias="is_valid")
    duplicateRecordsCount: int = Field(alias="duplicate_records_count")
    orphanReferencesCount: int = Field(alias="orphan_references_count")
    studentsWithZeroEnrollmentsCount: int = Field(alias="students_with_zero_enrollments_count")
    subjectsWithZeroEnrollmentsCount: int = Field(alias="subjects_with_zero_enrollments_count")
    cyclesWithZeroExamsCount: int = Field(alias="cycles_with_zero_exams_count")
    details: dict[str, Any] = Field(default_factory=dict)
