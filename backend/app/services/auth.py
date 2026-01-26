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
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
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
        # First, optionally revoke old tokens to prevent buildup (simple policy)
        # For now, just create new one
        db_refresh = RefreshToken(
            token_hash=hashed_refresh,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),  # Fixed duration, should match config
        )

        # Need to import config to get actual duration
        from app.core.config import get_settings

        settings = get_settings()
        db_refresh.expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
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
        # We need to query by user_id and verify hash
        # This is slightly inefficient (fetching all user's tokens), but safe
        # Better: Store token ID in JWT? No, stateless.
        # Alternatively: Store hash of raw token? Yes we did that.
        # But we can't query by hash easily because Argon2 is salted randomly.
        # So we have to iterate user's active tokens.

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


auth_service = AuthService()
