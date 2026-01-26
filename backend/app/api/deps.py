"""API dependencies for dependency injection."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import TokenInvalidError, InactiveUserError
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth import TokenPayload

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


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
