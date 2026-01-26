"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession, get_current_user
from app.core.security import (
    create_mfa_temp_token,
    generate_totp_secret,
    get_totp_uri,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFAEnrollResponse,
    MFARequiredResponse,
    MFAValidateRequest,
    MFAVerifyRequest,
    RefreshRequest,
    Token,
)
from app.services.auth import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=Token | MFARequiredResponse,
    summary="Login with email and password",
    description="Authenticate user. Returns Access Token OR MFA Challenge if enabled.",
)
async def login(
    login_data: LoginRequest,
    db: DbSession,
) -> Token | MFARequiredResponse:
    """Login with email and password."""
    user = auth_service.authenticate(db, login_data)

    if user.mfa_enabled:
        temp_token = create_mfa_temp_token(user.id)
        return MFARequiredResponse(temp_token=temp_token)

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
    """Login using form data (for Swagger UI).

    Note: Swagger UI doesn't support the MFA flow well, so this assumes MFA is disabled
    or fails if MFA is enabled.
    """
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    user = auth_service.authenticate(db, login_data)

    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is enabled. Please use the /login endpoint or MFA flow.",
        )

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


@router.post(
    "/mfa/enroll",
    response_model=MFAEnrollResponse,
    summary="Enroll in MFA",
    description="Generate a new TOTP secret and QR code URI.",
)
async def mfa_enroll(
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> MFAEnrollResponse:
    """Start MFA enrollment."""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )

    secret = generate_totp_secret()
    current_user.mfa_secret = secret
    db.commit()

    uri = get_totp_uri(current_user.email, secret)
    return MFAEnrollResponse(secret=secret, provisioning_uri=uri)


@router.post(
    "/mfa/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify MFA enrollment",
    description="Verify the TOTP code and enable MFA for the user.",
)
async def mfa_verify(
    verify_data: MFAVerifyRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Finalize MFA enrollment."""
    if current_user.mfa_enabled:
        return {"message": "MFA is already enabled"}

    auth_service.enable_mfa(db, current_user, verify_data.code)
    return {"message": "MFA enabled successfully"}


@router.post(
    "/mfa/validate",
    response_model=Token,
    summary="Validate MFA login",
    description="Complete the login process by providing the MFA code and temp token.",
)
async def mfa_validate(
    validate_data: MFAValidateRequest,
    db: DbSession,
) -> Token:
    """Validate MFA code and issue tokens."""
    return auth_service.validate_mfa_login(
        db, validate_data.temp_token, validate_data.code
    )
