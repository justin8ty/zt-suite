"""Agent token Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentTokenCreate(BaseModel):
    """Request schema for issuing an agent token."""

    name: str = Field(default="default agent", min_length=1, max_length=100)


class AgentTokenRead(BaseModel):
    """Agent token metadata without the raw token secret."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    name: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class AgentTokenIssued(AgentTokenRead):
    """Response schema returned once when an agent token is issued."""

    token: str
