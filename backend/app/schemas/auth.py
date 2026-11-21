from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleEnum, UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    email: str
    fullName: str = Field(alias="full_name")
    role: RoleEnum
    departmentId: str | None = Field(default=None, alias="department_id")
    studentId: str | None = None
    status: UserStatus

    # Also expose snake_case properties for compatibility
    @property
    def full_name(self) -> str:
        return self.fullName

    @property
    def department_id(self) -> str | None:
        return self.departmentId


class TokenResponse(BaseModel):
    accessToken: str = Field(alias="access_token")
    tokenType: str = Field(default="bearer", alias="token_type")
    expiresIn: int = Field(alias="expires_in")
    user: UserProfileResponse


class MessageResponse(BaseModel):
    message: str
