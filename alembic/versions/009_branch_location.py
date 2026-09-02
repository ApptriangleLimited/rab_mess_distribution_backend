"""Add branch_location to members and sender accounts.

Revision ID: 009_branch_location
Revises: 008_sender_active
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_branch_location"
down_revision: Union[str, None] = "008_sender_active"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "members",
        sa.Column("branch_location", sa.String(128), nullable=False, server_default=""),
    )
    op.add_column(
        "sender_accounts",
        sa.Column("branch_location", sa.String(120), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("sender_accounts", "branch_location")
    op.drop_column("members", "branch_location")
