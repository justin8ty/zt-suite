"""Access Log ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccessLog(Base):
    """Audit log for access events.

    Attributes:
        id: Primary key.
        user_id: User who performed the action (nullable).
        action: Event type (e.g., login, access_denied).
        resource: Target resource or endpoint.
        ip_address: Client IP address.
        user_agent: Client User-Agent string.
        status: Outcome (success/failure).
        details: Additional context (JSON/text).
        timestamp: When the event occurred.
    """

    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failure
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<AccessLog(action='{self.action}', status='{self.status}')>"
