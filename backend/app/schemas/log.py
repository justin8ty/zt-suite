"""Access Log Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccessLogRead(BaseModel):
    """Schema for reading access logs."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    resource: str | None
    ip_address: str | None
    status: str
    details: str | None
    timestamp: datetime


class AccessLogList(BaseModel):
    """Paginated list of access logs."""

    logs: list[AccessLogRead]
    total: int
