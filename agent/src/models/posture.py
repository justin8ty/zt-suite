"""Endpoint posture data models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NetworkInterface(BaseModel):
    """Network interface details collected from the endpoint."""

    name: str
    ip_addresses: list[str] = Field(default_factory=list)
    mac_address: str | None = None
    is_up: bool


class SecurityStatus(BaseModel):
    """Best-effort endpoint security posture status.

    Values are nullable because availability differs by OS, distribution,
    permissions, and installed security tooling.
    """

    firewall_enabled: bool | None = None
    antivirus_present: bool | None = None
    disk_encryption_enabled: bool | None = None
    updates_available: bool | None = None
    check_details: dict[str, str] = Field(default_factory=dict)


class PostureReport(BaseModel):
    """Endpoint posture report produced by the local agent."""

    agent_id: str
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    uptime_seconds: int
    boot_time: datetime
    collected_at: datetime
    agent_version: str
    network_interfaces: list[NetworkInterface]
    security: SecurityStatus


PostureOutputType = Literal["posture"]


class PostureEnvelope(BaseModel):
    """JSONL envelope for locally written posture reports."""

    type: PostureOutputType = "posture"
    report: PostureReport
