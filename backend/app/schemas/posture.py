"""Posture Report Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostureReportBase(BaseModel):
    """Base posture report schema."""

    antivirus_present: bool
    antivirus_enabled: bool
    firewall_enabled: bool
    disk_encrypted: bool
    os_up_to_date: bool


class PostureReportCreate(PostureReportBase):
    """Schema for submitting a posture report."""

    pass


class PostureReportRead(PostureReportBase):
    """Schema for reading posture reports."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    compliance_score: int
    is_compliant: bool
    timestamp: datetime
