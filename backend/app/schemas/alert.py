"""Alert Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    """Base alert schema."""

    severity: str
    category: str
    title: str
    description: str
    source_ip: str | None = None


class AlertCreate(AlertBase):
    """Schema for creating an alert."""

    device_id: int


class AlertUpdate(BaseModel):
    """Schema for updating/acknowledging an alert."""

    is_acknowledged: bool


class AlertRead(AlertBase):
    """Schema for reading alerts."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    is_acknowledged: bool
    acknowledged_by: int | None
    acknowledged_at: datetime | None
    timestamp: datetime
