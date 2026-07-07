"""Posture Report Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostureReportBase(BaseModel):
    """Base posture report schema."""

    antivirus_present: bool
    antivirus_enabled: bool
    firewall_enabled: bool
    disk_encrypted: bool
    os_up_to_date: bool | None = None


class PostureReportCreate(PostureReportBase):
    """Schema for submitting a posture report."""

    check_details: dict[str, str] | None = None
    hostname: str | None = None
    os_type: str | None = None
    os_version: str | None = None
    agent_version: str | None = None


class PostureReportRead(PostureReportBase):
    """Schema for reading posture reports."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    compliance_score: int
    is_compliant: bool
    timestamp: datetime
    check_details: str | None = None
