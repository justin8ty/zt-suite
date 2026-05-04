"""Traffic Record ORM model."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrafficRecord(Base):
    """Network traffic metadata record.

    Optimized for bulk insertion and time-series querying.
    """

    __tablename__ = "traffic_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), nullable=False, index=True
    )

    # 5-tuple + metadata
    src_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    dst_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    src_port: Mapped[int] = mapped_column(Integer, nullable=False)
    dst_port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), nullable=False)  # TCP, UDP

    # Stats
    bytes_sent: Mapped[int] = mapped_column(Integer, default=0)
    bytes_received: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamp (Indexed for range queries)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), index=True
    )

    # Relationships
    device: Mapped["Device"] = relationship()

    def __repr__(self) -> str:
        return f"<TrafficRecord({self.src_ip} -> {self.dst_ip}:{self.dst_port})>"
