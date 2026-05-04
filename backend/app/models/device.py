"""Device ORM model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    """Device/Endpoint model.

    Attributes:
        id: Primary key.
        hostname: Machine hostname.
        os_type: OS type (windows, linux, macos).
        os_version: OS version string.
        agent_version: Version of the agent software.
        last_seen: Timestamp of last activity/heartbeat.
        is_compliant: Cached compliance status.
        user_id: Owner user ID (optional).
    """

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    os_type: Mapped[str] = mapped_column(String(50), nullable=False)
    os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship()
    posture_reports: Mapped[list["PostureReport"]] = relationship(
        back_populates="device"
    )

    def __repr__(self) -> str:
        return f"<Device(hostname='{self.hostname}', compliant={self.is_compliant})>"
