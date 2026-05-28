"""improve_posture_fidelity_fields

Revision ID: 2f4a6b8c9d11
Revises: 9c3e5a7b2d10
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f4a6b8c9d11"
down_revision: Union[str, Sequence[str], None] = "9c3e5a7b2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("posture_reports", schema=None) as batch_op:
        batch_op.alter_column(
            "os_up_to_date",
            existing_type=sa.Boolean(),
            nullable=True,
        )
        batch_op.add_column(sa.Column("check_details", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("posture_reports", schema=None) as batch_op:
        batch_op.drop_column("check_details")
        batch_op.alter_column(
            "os_up_to_date",
            existing_type=sa.Boolean(),
            nullable=False,
        )
