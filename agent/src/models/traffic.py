"""Traffic capture data models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TCPFlags(BaseModel):
    """TCP flag states extracted from packet header."""

    syn: bool = False
    ack: bool = False
    fin: bool = False
    rst: bool = False
    psh: bool = False
    urg: bool = False


class TrafficRecord(BaseModel):
    """Metadata extracted from a captured network packet.

    Contains only metadata - no payload content is captured.
    This record is designed for anomaly detection feature engineering.
    """

    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: Literal["TCP", "UDP"]
    packet_size: int
    tcp_flags: TCPFlags | None = None  # None for UDP packets


class TrafficBatchEnvelope(BaseModel):
    """Envelope for batched traffic records."""

    type: Literal["traffic_batch"] = "traffic_batch"
    agent_id: str
    batch_id: str
    record_count: int = Field(ge=0)
    flushed_at: datetime
    emergency: bool = False
    records: list[TrafficRecord]
