"""Agent token ORM model for device-scoped telemetry authentication."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.device import Device


class AgentToken(Base, TimestampMixin):
    """Device-scoped token used by an endpoint agent.

    Attributes:
        id: Primary key.
        token_hash: Deterministic hash of the raw agent token.
        device_id: Device this token is allowed to report for.
        name: Human-readable token label.
        last_used_at: Last successful use timestamp.
        revoked_at: Timestamp when token was revoked.
    """

    __tablename__ = "agent_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    device: Mapped["Device"] = relationship()
