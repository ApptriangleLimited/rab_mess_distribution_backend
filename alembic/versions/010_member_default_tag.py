"""Add members.default_tag for standing duty projection.

Revision ID: 010_member_default_tag
Revises: 009_branch_location
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_member_default_tag"
down_revision: Union[str, None] = "009_branch_location"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "members",
        sa.Column(
            "default_tag",
            sa.String(16),
            nullable=False,
            server_default="MS",
        ),
    )


def downgrade() -> None:
    op.drop_column("members", "default_tag")
