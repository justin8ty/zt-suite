"""Security utilities for password hashing, JWT, and TOTP."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context using Argon2id
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token.

    Args:
        subject: Subject identifier (usually user ID).
        expires_delta: Optional expiration time delta.

    Returns:
        Encoded JWT string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> tuple[str, str]:
    """Create a refresh token.

    Returns:
        Tuple of (raw_token, hashed_token).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    # We use a random string for refresh token, but JWT format is convenient
    # for stateless validation if needed later. For now, we store hash in DB.
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    raw_token = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    # Hash the token for storage
    # Use sha256 via passlib (faster than argon2 for tokens) or just argon2
    # Since we already have argon2 setup, we'll use it but with lower parameters
    # for speed if possible, or just standard verify.
    # Actually, for refresh tokens, a fast hash like SHA256 is better than Argon2
    # because we look it up frequently. But let's stick to pwd_context for simplicity
    # and consistency in FYP.
    hashed_token = hash_password(raw_token)

    return raw_token, hashed_token


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except Exception:
        return None
