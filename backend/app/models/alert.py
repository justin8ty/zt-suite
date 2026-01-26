"""Alert ORM model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    """Security alert/anomaly record.

    Attributes:
        id: Primary key.
        device_id: FK to Device.
        severity: low, medium, high, critical.
        category: anomaly, policy, malware.
        description: Text detail.
        is_acknowledged: Has an admin seen/resolved this?
        acknowledged_by: User ID of admin (optional).
        timestamp: Detection time.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)

    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Context (optional source of alert)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Workflow
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), index=True
    )

    # Relationships
    device: Mapped["Device"] = relationship()
    resolver: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Alert({self.severity}, {self.title})>"
