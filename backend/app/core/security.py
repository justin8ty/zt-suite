"""Security utilities for password hashing, JWT, and TOTP."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any

import pyotp
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


def generate_totp_secret() -> str:
    """Generate a random base32 secret for TOTP."""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against a secret.

    Args:
        secret: The base32 secret.
        code: The 6-digit code provided by the user.

    Returns:
        True if valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def get_totp_uri(account_name: str, secret: str) -> str:
    """Generate the provisioning URI for TOTP.

    Args:
        account_name: User's email or username.
        secret: The base32 secret.

    Returns:
        otpauth:// URI string.
    """
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=settings.mfa_issuer_name
    )


def _hash_secret_token(token: str, purpose: str) -> str:
    """Create a deterministic keyed hash for secret token lookup."""
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        f"{purpose}:{token}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_trusted_device_token() -> str:
    """Generate a random trusted-device token."""
    return secrets.token_urlsafe(32)


def hash_trusted_device_token(token: str) -> str:
    """Create a deterministic keyed hash for trusted-device token lookup."""
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_agent_token() -> str:
    """Generate a random agent API token."""
    return f"ztag_{secrets.token_urlsafe(32)}"


def hash_agent_token(token: str) -> str:
    """Create a deterministic keyed hash for agent token lookup."""
    return _hash_secret_token(token, "agent")


def create_mfa_temp_token(subject: str | Any) -> str:
    """Create a temporary token for MFA validation step.

    This token is short-lived and only valid for the /mfa/validate endpoint.
    It cannot be used for accessing protected resources.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {"exp": expire, "sub": str(subject), "type": "mfa_pending"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt
