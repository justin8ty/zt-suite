"""Authentication Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT Token payload schema."""

    sub: int | None = None
    type: str | None = None


class RefreshRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
