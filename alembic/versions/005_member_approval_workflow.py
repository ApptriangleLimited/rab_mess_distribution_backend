"""member approval workflow: created_via + approval_status backfill

Revision ID: 005_member_approval_workflow
Revises: 004_users_email_mess_rab
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_member_approval_workflow"
down_revision: Union[str, None] = "004_users_email_mess_rab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "members",
        sa.Column(
            "created_via",
            sa.String(32),
            nullable=False,
            server_default="cc_staff",
        ),
    )

    # Legacy single `pending` → Daily queue; `accepted` → `approved`.
    op.execute(
        sa.text(
            "UPDATE members SET approval_status = 'pending_daily' "
            "WHERE approval_status = 'pending'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE members SET approval_status = 'approved' "
            "WHERE approval_status = 'accepted'"
        )
    )

    op.create_index("ix_members_approval_status", "members", ["approval_status"])
    op.create_index("ix_members_created_via", "members", ["created_via"])


def downgrade() -> None:
    op.drop_index("ix_members_created_via", table_name="members")
    op.drop_index("ix_members_approval_status", table_name="members")

    op.execute(
        sa.text(
            "UPDATE members SET approval_status = 'pending' "
            "WHERE approval_status IN ('pending_cc', 'pending_daily')"
        )
    )

    op.drop_column("members", "created_via")
