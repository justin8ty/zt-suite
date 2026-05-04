"""Traffic Record Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrafficRecordBase(BaseModel):
    """Base traffic record schema."""

    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes_sent: int = 0
    bytes_received: int = 0
    timestamp: datetime


class TrafficRecordCreate(TrafficRecordBase):
    """Schema for ingestion (single record)."""

    pass


class TrafficRecordRead(TrafficRecordBase):
    """Schema for reading traffic data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int


class TrafficBatchCreate(BaseModel):
    """Schema for batch ingestion."""

    device_id: int
    records: list[TrafficRecordCreate]
