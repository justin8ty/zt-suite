"""Role Pydantic schemas."""

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema."""

    name: str = Field(..., description="Role name (admin, user, viewer)")
    description: str | None = Field(None, description="Role description")


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleRead(RoleBase):
    """Schema for reading role data."""

    id: int

    class Config:
        from_attributes = True
