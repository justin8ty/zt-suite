"""Posture Report ORM model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PostureReport(Base):
    """Device security posture report.

    Attributes:
        id: Primary key.
        device_id: Foreign key to device.
        antivirus_present: Is AV installed?
        antivirus_enabled: Is AV active?
        firewall_enabled: Is firewall active?
        disk_encrypted: Is disk encrypted?
        os_up_to_date: Is OS patched?
        compliance_score: Calculated score (0-100).
        is_compliant: Result of evaluation.
        timestamp: Collection time.
    """

    __tablename__ = "posture_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)

    # Security checks
    antivirus_present: Mapped[bool] = mapped_column(Boolean, default=False)
    antivirus_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    firewall_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    disk_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    os_up_to_date: Mapped[bool] = mapped_column(Boolean, default=False)

    # Result
    compliance_score: Mapped[int] = mapped_column(Integer, default=0)
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), index=True
    )

    # Relationships
    device: Mapped["Device"] = relationship(back_populates="posture_reports")

    def __repr__(self) -> str:
        return f"<PostureReport(device_id={self.device_id}, compliant={self.is_compliant})>"
