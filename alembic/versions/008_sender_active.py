"""Add active flag to sender accounts.

Revision ID: 008_sender_active
Revises: 007_settings_senders
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_sender_active"
down_revision: Union[str, None] = "007_settings_senders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sender_accounts",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("sender_accounts", "active")
