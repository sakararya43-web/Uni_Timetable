from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import EntityStatus


# ==============================================================================
# Department Schemas
# ==============================================================================
class DepartmentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=255)


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    status: EntityStatus | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    code: str
    name: str
    status: EntityStatus


class PaginatedDepartmentsResponse(BaseModel):
    items: list[DepartmentResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


# ==============================================================================
# Academic Year Schemas
# ==============================================================================
class AcademicYearCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=4, max_length=64)  # e.g. "2026-2027"
    startDate: date = Field(alias="start_date")
    endDate: date = Field(alias="end_date")

    @model_validator(mode="after")
    def validate_dates(self) -> "AcademicYearCreate":
        if self.endDate < self.startDate:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class AcademicYearUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=4, max_length=64)
    startDate: date | None = Field(default=None, alias="start_date")
    endDate: date | None = Field(default=None, alias="end_date")
    status: EntityStatus | None = None


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    startDate: date = Field(alias="start_date")
    endDate: date = Field(alias="end_date")
    status: EntityStatus


class PaginatedAcademicYearsResponse(BaseModel):
    items: list[AcademicYearResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


# ==============================================================================
# Semester Schemas
# ==============================================================================
class SemesterCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    academicYearId: str = Field(alias="academic_year_id")
    name: str = Field(min_length=2, max_length=64)
    number: int = Field(ge=1, le=16)


class SemesterUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=2, max_length=64)
    number: int | None = Field(default=None, ge=1, le=16)
    status: EntityStatus | None = None


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    academicYearId: str = Field(alias="academic_year_id")
    name: str
    number: int
    status: EntityStatus


class PaginatedSemestersResponse(BaseModel):
    items: list[SemesterResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


# ==============================================================================
# Program Schemas
# ==============================================================================
class ProgramCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    departmentId: str = Field(alias="department_id")
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=255)


class ProgramUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    status: EntityStatus | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    departmentId: str = Field(alias="department_id")
    code: str
    name: str
    status: EntityStatus


class PaginatedProgramsResponse(BaseModel):
    items: list[ProgramResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
