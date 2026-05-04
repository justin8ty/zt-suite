"""User ORM model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Avoid circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role


class User(Base, TimestampMixin):
    """User account model.

    Attributes:
        id: Primary key.
        email: Unique email address (used for login).
        password_hash: Argon2id hashed password.
        is_active: Whether the user account is active.
        mfa_secret: TOTP secret for MFA (encrypted base32 string).
        mfa_enabled: Whether MFA is enabled for this user.
        created_at: Timestamp when user was created.
        updated_at: Timestamp when user was last updated.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",  # Eager load roles
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
