"""Authentication API routes."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.services.auth import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
    description="Authenticate user and return access/refresh tokens.",
)
async def login(
    login_data: LoginRequest,
    db: DbSession,
) -> Token:
    """Login with email and password."""
    user = auth_service.authenticate(db, login_data)
    return auth_service.create_tokens(db, user)


# Support for Swagger UI "Authorize" button (OAuth2 form data)
@router.post(
    "/login/form",
    response_model=Token,
    include_in_schema=False,
)
async def login_form(
    db: DbSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Login using form data (for Swagger UI)."""
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    user = auth_service.authenticate(db, login_data)
    return auth_service.create_tokens(db, user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get new access/refresh tokens using a valid refresh token.",
)
async def refresh_token(
    refresh_data: RefreshRequest,
    db: DbSession,
) -> Token:
    """Refresh access token."""
    return auth_service.refresh_token(db, refresh_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revoke the refresh token.",
)
async def logout(
    refresh_data: RefreshRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout user."""
    auth_service.logout(db, refresh_data.refresh_token)
