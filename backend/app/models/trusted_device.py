"""Trusted device ORM model for MFA bypass."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class TrustedDevice(Base, TimestampMixin):
    """Trusted browser/device token that can bypass MFA temporarily.

    Attributes:
        id: Primary key.
        token_hash: Deterministic hash of the raw device token.
        user_id: User who trusted this browser/device.
        device_label: Human-readable label supplied by the client.
        expires_at: Expiration timestamp.
        last_used_at: Last successful MFA bypass timestamp.
        revoked_at: Timestamp when trust was revoked.
    """

    __tablename__ = "trusted_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    user: Mapped["User"] = relationship()
