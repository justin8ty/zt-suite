"""create_network_flows_table

Revision ID: c7f0a2e4b6d3
Revises: 2f4a6b8c9d11
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7f0a2e4b6d3"
down_revision: Union[str, Sequence[str], None] = "2f4a6b8c9d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "network_flows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("src_ip", sa.String(length=45), nullable=True),
        sa.Column("dst_ip", sa.String(length=45), nullable=True),
        sa.Column("src_port", sa.Integer(), nullable=True),
        sa.Column("dst_port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(length=20), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("flow_duration", sa.Float(), nullable=True),
        sa.Column("total_fwd_packets", sa.Integer(), nullable=True),
        sa.Column("total_bwd_packets", sa.Integer(), nullable=True),
        sa.Column("total_fwd_bytes", sa.Integer(), nullable=True),
        sa.Column("total_bwd_bytes", sa.Integer(), nullable=True),
        sa.Column("malicious_score", sa.Float(), nullable=True),
        sa.Column("prediction", sa.Integer(), nullable=True),
        sa.Column("prediction_label", sa.String(length=50), nullable=True),
        sa.Column("detection_source", sa.String(length=50), nullable=False),
        sa.Column("raw_features_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("network_flows", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_network_flows_batch_id"), ["batch_id"])
        batch_op.create_index(batch_op.f("ix_network_flows_device_id"), ["device_id"])
        batch_op.create_index(batch_op.f("ix_network_flows_dst_ip"), ["dst_ip"])
        batch_op.create_index(batch_op.f("ix_network_flows_src_ip"), ["src_ip"])
        batch_op.create_index(batch_op.f("ix_network_flows_timestamp"), ["timestamp"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("network_flows", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_network_flows_timestamp"))
        batch_op.drop_index(batch_op.f("ix_network_flows_src_ip"))
        batch_op.drop_index(batch_op.f("ix_network_flows_dst_ip"))
        batch_op.drop_index(batch_op.f("ix_network_flows_device_id"))
        batch_op.drop_index(batch_op.f("ix_network_flows_batch_id"))
    op.drop_table("network_flows")
