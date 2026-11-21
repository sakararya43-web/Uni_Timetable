import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import EntityStatus

STUDENT_NUMBER_REGEX = re.compile(r"^[A-Za-z0-9_-]{2,32}$")


class StudentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    studentNumber: str = Field(min_length=2, max_length=64, alias="student_number")
    fullName: str = Field(min_length=2, max_length=255, alias="full_name")
    email: EmailStr | None = None
    departmentId: str = Field(alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int = Field(ge=1, le=16)

    @field_validator("studentNumber")
    @classmethod
    def validate_student_number(cls, v: str) -> str:
        if not STUDENT_NUMBER_REGEX.match(v.strip()):
            raise ValueError(
                "student_number must be 2-32 alphanumeric characters, dashes, or underscores."
            )
        return v.strip().upper()


class StudentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fullName: str | None = Field(default=None, min_length=2, max_length=255, alias="full_name")
    email: EmailStr | None = None
    departmentId: str | None = Field(default=None, alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int | None = Field(default=None, ge=1, le=16)
    status: EntityStatus | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    studentNumber: str = Field(alias="student_number")
    fullName: str = Field(alias="full_name")
    email: str | None = None
    departmentId: str = Field(alias="department_id")
    programId: str | None = Field(default=None, alias="program_id")
    semester: int
    userId: str | None = Field(default=None, alias="user_id")
    status: EntityStatus


class PaginatedStudentsResponse(BaseModel):
    items: list[StudentResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
