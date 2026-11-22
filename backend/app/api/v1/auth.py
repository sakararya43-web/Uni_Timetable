import secrets

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import extract_token, get_current_user
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.config.settings import get_settings
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, TokenResponse, UserProfileResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with email and password, setting secure httpOnly cookies."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    req_id = request_id_ctx_var.get()

    user, token, expires_in = auth_service.authenticate_user(
        db=db,
        email=body.email,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=req_id,
    )

    # Set httpOnly Secure Cookie for browser clients (ADR-001)
    is_production = settings.APP_ENV == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )

    # Set readable Anti-CSRF token cookie (Task P2.12)
    csrf_token = secrets.token_hex(16)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=expires_in,
        httponly=False,
        secure=is_production,
        samesite="lax",
        path="/",
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    token: str | None = Depends(extract_token),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Invalidate active session and clear authentication cookies."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    req_id = request_id_ctx_var.get()

    if token:
        try:
            current_user = get_current_user(request, token=token, db=db)
            auth_service.logout_user(
                db=db,
                token=token,
                user=current_user,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=req_id,
            )
        except Exception:
            pass

    # Clear cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="csrf_token", path="/")

    return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Return profile and role capabilities for the currently authenticated user."""
    return UserProfileResponse.model_validate(current_user)
