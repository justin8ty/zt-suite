"""API dependencies for dependency injection."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import TokenInvalidError, InactiveUserError
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.agent_token import AgentToken
from app.models.device import Device
from app.models.user import User
from app.services.agent_token import agent_token_service
from app.schemas.auth import TokenPayload

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
agent_bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session.

    Yields:
        Session: SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency to validate JWT and return current user.

    Args:
        db: Database session.
        token: JWT access token.

    Returns:
        Authenticated user model.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    try:
        payload = decode_token(token)
        if payload is None:
            raise TokenInvalidError()

        token_data = TokenPayload(**payload)

        if token_data.type != "access":
            raise TokenInvalidError()

        if token_data.sub is None:
            raise TokenInvalidError()

    except (JWTError, ValueError):
        raise TokenInvalidError()

    user = db.get(User, token_data.sub)
    if not user:
        raise TokenInvalidError()

    if not user.is_active:
        raise InactiveUserError()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_agent_token(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(agent_bearer_scheme),
) -> AgentToken:
    """Dependency to validate a device-scoped agent bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise TokenInvalidError()

    token = agent_token_service.get_valid_token(db, credentials.credentials)
    if not token:
        raise TokenInvalidError()

    return token


CurrentAgentToken = Annotated[AgentToken, Depends(get_current_agent_token)]


async def require_mfa(
    current_user: CurrentUser,
) -> User:
    """Dependency that enforces MFA to be enabled."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA required for this resource",
        )
    return current_user


async def get_compliant_device(
    db: DbSession,
    current_user: CurrentUser,
    x_device_id: int | None = Header(default=None, alias="X-Device-ID"),
) -> Device:
    """Dependency that verifies the request comes from a compliant device.

    Args:
        x_device_id: Device ID passed in header.
    """
    if not x_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-ID header missing",
        )

    device = db.get(Device, x_device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Check ownership (unless admin)
    # We check role name string to avoid circular import of RoleName enum
    is_admin = any(r.name == "admin" for r in current_user.roles)

    if device.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device does not belong to user",
        )

    if not device.is_compliant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not compliant",
        )

    return device
