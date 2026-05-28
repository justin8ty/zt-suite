"""Authentication API routes."""

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession, get_current_user
from app.core.security import (
    create_mfa_temp_token,
    generate_totp_secret,
    get_totp_uri,
)
from app.models.user import User
from app.schemas.auth import (
    AccessToken,
    LoginRequest,
    MFAEnrollResponse,
    MFARequiredResponse,
    MFAValidateRequest,
    MFAVerifyRequest,
    RefreshRequest,
    Token,
)
from app.schemas.user import UserRead
from app.services.access_log import access_log_service
from app.services.auth import auth_service
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """Attach refresh token as an HttpOnly cookie."""
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
    )


def clear_refresh_token_cookie(response: Response) -> None:
    """Remove refresh token cookie from the browser."""
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
    )


def resolve_refresh_token(
    refresh_data: RefreshRequest | None, refresh_token_cookie: str | None
) -> str:
    """Read refresh token from HttpOnly cookie, with request body fallback for API clients."""
    if refresh_token_cookie:
        return refresh_token_cookie
    if refresh_data and refresh_data.refresh_token:
        return refresh_data.refresh_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token missing",
    )


def set_trusted_device_cookie(response: Response, token: str) -> None:
    """Attach trusted-device token as an HttpOnly cookie."""
    response.set_cookie(
        key=settings.trusted_device_cookie_name,
        value=token,
        max_age=settings.trusted_device_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.trusted_device_cookie_secure,
        samesite=settings.trusted_device_cookie_samesite,
    )


@router.post(
    "/login",
    response_model=AccessToken | MFARequiredResponse,
    summary="Login with email and password",
    description="Authenticate user. Returns Access Token OR MFA Challenge if enabled.",
)
async def login(
    login_data: LoginRequest,
    db: DbSession,
    response: Response,
    trusted_device_token: str | None = Cookie(
        default=None, alias=settings.trusted_device_cookie_name
    ),
) -> Token | MFARequiredResponse:
    """Login with email and password."""
    try:
        user = auth_service.authenticate(db, login_data)

        if user.mfa_enabled:
            trusted_device = auth_service.get_valid_trusted_device(
                db, user, trusted_device_token
            )
            if trusted_device:
                access_log_service.log_access(
                    db=db,
                    action="login_success_trusted_device",
                    status="success",
                    user_id=user.id,
                    resource="/api/auth/login",
                    details=f"MFA bypassed by trusted device {trusted_device.id}",
                )
                tokens = auth_service.create_tokens(db, user)
                set_refresh_token_cookie(response, tokens.refresh_token)
                return tokens

            if trusted_device_token:
                access_log_service.log_access(
                    db=db,
                    action="trusted_device_invalid",
                    status="failure",
                    user_id=user.id,
                    resource="/api/auth/login",
                    details="Trusted device token missing, expired, revoked, or invalid",
                )

            temp_token = create_mfa_temp_token(user.id)
            access_log_service.log_access(
                db=db,
                action="login_challenge_mfa",
                status="success",
                user_id=user.id,
                resource="/api/auth/login",
                details="MFA challenge issued",
            )
            return MFARequiredResponse(temp_token=temp_token)

        access_log_service.log_access(
            db=db,
            action="login_success",
            status="success",
            user_id=user.id,
            resource="/api/auth/login",
        )
        tokens = auth_service.create_tokens(db, user)
        set_refresh_token_cookie(response, tokens.refresh_token)
        return tokens

    except HTTPException as e:
        # Try to find user ID for logging if possible (not easy here without re-querying)
        # We'll log with user_id=None for failed logins to avoid enumeration assistance in logs
        access_log_service.log_access(
            db=db,
            action="login_failed",
            status="failure",
            resource="/api/auth/login",
            details=str(e.detail),
        )
        raise e


# Support for Swagger UI "Authorize" button (OAuth2 form data)
@router.post(
    "/login/form",
    response_model=AccessToken,
    include_in_schema=False,
)
async def login_form(
    db: DbSession,
    response: Response,
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

    tokens = auth_service.create_tokens(db, user)
    set_refresh_token_cookie(response, tokens.refresh_token)
    return tokens


@router.post(
    "/refresh",
    response_model=AccessToken,
    summary="Refresh access token",
    description="Get new access token using the HttpOnly refresh-token cookie.",
)
async def refresh_token(
    db: DbSession,
    response: Response,
    refresh_data: RefreshRequest | None = Body(default=None),
    refresh_token_cookie: str | None = Cookie(
        default=None, alias=settings.refresh_token_cookie_name
    ),
) -> Token:
    """Refresh access token."""
    refresh_token_value = resolve_refresh_token(refresh_data, refresh_token_cookie)
    tokens = auth_service.refresh_token(db, refresh_token_value)
    set_refresh_token_cookie(response, tokens.refresh_token)
    return tokens


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Return the authenticated user's profile and roles.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Get the current authenticated user."""
    return UserRead.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revoke the refresh token.",
)
async def logout(
    db: DbSession,
    response: Response,
    refresh_data: RefreshRequest | None = Body(default=None),
    refresh_token_cookie: str | None = Cookie(
        default=None, alias=settings.refresh_token_cookie_name
    ),
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout user."""
    try:
        refresh_token_value = resolve_refresh_token(refresh_data, refresh_token_cookie)
        auth_service.logout(db, refresh_token_value)
    finally:
        clear_refresh_token_cookie(response)

    access_log_service.log_access(
        db=db,
        action="logout",
        status="success",
        user_id=current_user.id,
        resource="/api/auth/logout",
    )


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
    response_model=AccessToken,
    summary="Validate MFA login",
    description="Complete the login process by providing the MFA code and temp token.",
)
async def mfa_validate(
    validate_data: MFAValidateRequest,
    db: DbSession,
    response: Response,
) -> Token:
    """Validate MFA code and issue tokens."""
    try:
        tokens, user = auth_service.validate_mfa_login(
            db, validate_data.temp_token, validate_data.code
        )

        set_refresh_token_cookie(response, tokens.refresh_token)

        if validate_data.trust_device:
            raw_token, trusted_device = auth_service.create_trusted_device(
                db=db,
                user=user,
                device_label=validate_data.device_label,
            )
            set_trusted_device_cookie(response, raw_token)
            details = f"MFA completed; trusted device {trusted_device.id} created"
        else:
            details = "MFA completed"

        access_log_service.log_access(
            db=db,
            action="mfa_login_success",
            status="success",
            user_id=user.id,
            resource="/api/auth/mfa/validate",
            details=details,
        )
        return tokens

    except HTTPException as e:
        access_log_service.log_access(
            db=db,
            action="mfa_login_failed",
            status="failure",
            resource="/api/auth/mfa/validate",
            details=str(e.detail),
        )
        raise e
