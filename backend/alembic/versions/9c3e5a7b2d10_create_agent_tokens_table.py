"""create_agent_tokens_table

Revision ID: 9c3e5a7b2d10
Revises: 8b6a8b2c4d1f
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c3e5a7b2d10"
down_revision: Union[str, Sequence[str], None] = "8b6a8b2c4d1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "agent_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agent_tokens", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_agent_tokens_device_id"), ["device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_agent_tokens_token_hash"), ["token_hash"], unique=True
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("agent_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agent_tokens_token_hash"))
        batch_op.drop_index(batch_op.f("ix_agent_tokens_device_id"))

    op.drop_table("agent_tokens")
