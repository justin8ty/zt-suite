"""Traffic feature engineering data models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TrafficFeatureVector(BaseModel):
    """Model-ready feature vector derived from a traffic batch."""

    agent_id: str
    batch_id: str
    window_start: datetime
    window_end: datetime
    duration_seconds: float = Field(ge=0)
    packet_count: int = Field(ge=0)
    byte_count: int = Field(ge=0)
    packets_per_minute: float = Field(ge=0)
    bytes_per_minute: float = Field(ge=0)
    unique_dst_ip_count: int = Field(ge=0)
    unique_dst_port_count: int = Field(ge=0)
    average_packet_size: float = Field(ge=0)
    tcp_packet_count: int = Field(ge=0)
    udp_packet_count: int = Field(ge=0)
    syn_ratio: float = Field(ge=0, le=1)
    ack_ratio: float = Field(ge=0, le=1)
    fin_ratio: float = Field(ge=0, le=1)
    rst_ratio: float = Field(ge=0, le=1)
    psh_ratio: float = Field(ge=0, le=1)
    urg_ratio: float = Field(ge=0, le=1)
    well_known_port_ratio: float = Field(ge=0, le=1)
    ephemeral_port_ratio: float = Field(ge=0, le=1)


class TrafficFeatureEnvelope(BaseModel):
    """JSONL envelope for locally written traffic features."""

    type: Literal["traffic_features"] = "traffic_features"
    features: TrafficFeatureVector
