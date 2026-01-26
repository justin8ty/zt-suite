"""User Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )


class UserUpdate(BaseModel):
    """Schema for updating a user. All fields optional."""

    email: EmailStr | None = Field(None, description="New email address")
    password: str | None = Field(
        None,
        min_length=8,
        max_length=128,
        description="New password (min 8 characters)",
    )
    is_active: bool | None = Field(None, description="Account active status")


class UserRead(UserBase):
    """Schema for reading user data (response)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether account is active")
    mfa_enabled: bool = Field(..., description="Whether MFA is enabled")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserList(BaseModel):
    """Schema for paginated user list response."""

    users: list[UserRead]
    total: int = Field(..., description="Total number of users")
