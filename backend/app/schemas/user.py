from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleEnum, UserStatus
from app.schemas.auth import UserProfileResponse


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    password: str = Field(min_length=8)
    fullName: str = Field(min_length=2, max_length=255, alias="full_name")
    role: RoleEnum
    departmentId: str | None = Field(default=None, alias="department_id")


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fullName: str | None = Field(default=None, min_length=2, max_length=255, alias="full_name")
    role: RoleEnum | None = None
    departmentId: str | None = Field(default=None, alias="department_id")
    status: UserStatus | None = None


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    newPassword: str = Field(min_length=8, alias="new_password")


class PaginatedUsersResponse(BaseModel):
    items: list[UserProfileResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
