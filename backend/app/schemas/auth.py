"""Authentication Pydantic schemas."""

from pydantic import BaseModel, EmailStr


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


class MFAEnrollResponse(BaseModel):
    """MFA Enrollment response schema."""

    secret: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    """MFA Verification request schema."""

    code: str


class MFARequiredResponse(BaseModel):
    """Response when login requires MFA."""

    mfa_required: bool = True
    temp_token: str


class MFAValidateRequest(BaseModel):
    """MFA Validation request schema (Step 2 of login)."""

    temp_token: str
    code: str
    trust_device: bool = False
    device_label: str | None = None
