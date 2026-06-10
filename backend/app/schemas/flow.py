"""Network flow Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NetworkFlowBase(BaseModel):
    """Base network-flow fields persisted from agent flow mode."""

    batch_id: str
    src_ip: str | None = None
    dst_ip: str | None = None
    src_port: int | None = None
    dst_port: int | None = None
    protocol: str | None = None
    timestamp: datetime
    flow_duration: float | None = None
    total_fwd_packets: int | None = None
    total_bwd_packets: int | None = None
    total_fwd_bytes: int | None = None
    total_bwd_bytes: int | None = None
    malicious_score: float | None = None
    prediction: int | None = None
    prediction_label: str | None = None
    detection_source: str = "model"
    raw_features: dict[str, Any] = Field(default_factory=dict)


class NetworkFlowCreate(NetworkFlowBase):
    """Schema for ingesting one scored flow."""

    pass


class NetworkFlowRead(NetworkFlowBase):
    """Schema for reading stored scored flows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int


class NetworkFlowBatchCreate(BaseModel):
    """Schema for ingesting scored flow batches from an agent."""

    device_id: int
    batch_id: str
    flows: list[NetworkFlowCreate]
