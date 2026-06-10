"""Network flow ORM model."""

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.device import Device


class NetworkFlow(Base):
    """CICFlowMeter-derived network flow with model scoring metadata."""

    __tablename__ = "network_flows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), nullable=False, index=True
    )
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    src_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    dst_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), index=True
    )

    flow_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_fwd_packets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_bwd_packets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_fwd_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_bwd_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    malicious_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prediction_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detection_source: Mapped[str] = mapped_column(String(50), nullable=False)

    raw_features_json: Mapped[str] = mapped_column(Text, nullable=False)

    device: Mapped["Device"] = relationship()

    @property
    def raw_features(self) -> dict[str, Any]:
        """Decoded raw CICFlowMeter/scored row for API reads."""
        try:
            decoded = json.loads(self.raw_features_json)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}

    def __repr__(self) -> str:
        return f"<NetworkFlow({self.src_ip} -> {self.dst_ip}:{self.dst_port})>"
