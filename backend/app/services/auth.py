"""Authentication service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    TokenInvalidError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
    hash_password,
    verify_totp,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, TokenPayload
from app.services.user import user_service


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def authenticate(db: Session, login_data: LoginRequest) -> User:
        """Authenticate a user by email and password.

        Args:
            db: Database session.
            login_data: Login request data.

        Returns:
            Authenticated user.

        Raises:
            InvalidCredentialsError: If credentials are invalid.
            InactiveUserError: If user account is inactive.
        """
        user = user_service.get_by_email(db, login_data.email)

        if not user:
            # Prevent timing attacks by verifying a fake password
            # This is a valid Argon2id hash for "fake_password"
            verify_password(
                "fake",
                "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$Wfh+/GHx5K/J9j/9/yZ/8Q",
            )
            raise InvalidCredentialsError()

        if not verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        return user

    @staticmethod
    def create_tokens(db: Session, user: User) -> Token:
        """Create access and refresh tokens for a user.

        Args:
            db: Database session.
            user: User to create tokens for.

        Returns:
            Token response schema.
        """
        access_token = create_access_token(user.id)
        raw_refresh, hashed_refresh = create_refresh_token(user.id)

        # Store refresh token in DB
        db_refresh = RefreshToken(
            token_hash=hashed_refresh,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),  # Default, overwritten by config below
        )

        # Need to import config to get actual duration
        from app.core.config import get_settings

        settings = get_settings()
        db_refresh.expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

        db.add(db_refresh)
        db.commit()

        return Token(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
        )

    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> Token:
        """Refresh an access token using a refresh token.

        Args:
            db: Database session.
            refresh_token: Raw refresh token string.

        Returns:
            New token pair.

        Raises:
            TokenInvalidError: If token is invalid/expired/revoked.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise TokenInvalidError()

        user_id = int(payload["sub"])

        # Verify token exists in DB and is valid
        user_tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        ).all()

        valid_token_record = None
        for record in user_tokens:
            if verify_password(refresh_token, record.token_hash):
                valid_token_record = record
                break

        if not valid_token_record:
            raise TokenInvalidError()

        # Revoke the used refresh token (Rotation policy)
        valid_token_record.revoked = True
        valid_token_record.revoked_at = datetime.now(timezone.utc)

        # Issue new pair
        user = user_service.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise TokenInvalidError()

        return AuthService.create_tokens(db, user)

    @staticmethod
    def logout(db: Session, refresh_token: str) -> None:
        """Logout by revoking the refresh token.

        Args:
            db: Database session.
            refresh_token: Raw refresh token.
        """
        try:
            payload = decode_token(refresh_token)
            if not payload:
                return

            user_id = int(payload["sub"])

            # Find and revoke
            user_tokens = db.scalars(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked == False,  # noqa: E712
                )
            ).all()

            for record in user_tokens:
                if verify_password(refresh_token, record.token_hash):
                    record.revoked = True
                    record.revoked_at = datetime.now(timezone.utc)
                    db.commit()
                    break
        except Exception:
            # Fail silently on logout errors
            pass

    @staticmethod
    def enable_mfa(db: Session, user: User, code: str) -> bool:
        """Verify code and enable MFA for user.

        Args:
            db: Database session.
            user: User object.
            code: TOTP code.

        Returns:
            True if successful.

        Raises:
            InvalidCredentialsError: If code is invalid.
        """
        if not user.mfa_secret:
            raise InvalidCredentialsError()

        if not verify_totp(user.mfa_secret, code):
            raise InvalidCredentialsError()

        user.mfa_enabled = True
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def validate_mfa_login(db: Session, temp_token: str, code: str) -> Token:
        """Validate MFA login step 2.

        Args:
            db: Database session.
            temp_token: Temporary JWT from step 1.
            code: TOTP code.

        Returns:
            Access tokens.

        Raises:
            TokenInvalidError: If temp_token is invalid.
            InvalidCredentialsError: If code is invalid.
        """
        payload = decode_token(temp_token)
        if (
            not payload
            or payload.get("type") != "mfa_pending"
            or not payload.get("sub")
        ):
            raise TokenInvalidError()

        user_id = int(payload["sub"])
        user = user_service.get_by_id(db, user_id)

        if not user or not user.is_active:
            raise TokenInvalidError()

        if not user.mfa_enabled or not user.mfa_secret:
            # Should not happen if flow is correct, but fail safe
            raise InvalidCredentialsError()

        if not verify_totp(user.mfa_secret, code):
            raise InvalidCredentialsError()

        return AuthService.create_tokens(db, user)


auth_service = AuthService()
