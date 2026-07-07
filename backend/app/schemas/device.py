"""Device Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    """Base device schema."""

    hostname: str
    os_type: str = "unknown"
    os_version: str | None = None
    agent_version: str | None = None


class DeviceCreate(DeviceBase):
    """Schema for registering a device enrollment."""

    user_id: int | None = None


class DeviceRead(DeviceBase):
    """Schema for reading device data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    last_seen: datetime
    is_compliant: bool


class DeviceList(BaseModel):
    """Paginated list of devices."""

    devices: list[DeviceRead]
    total: int
