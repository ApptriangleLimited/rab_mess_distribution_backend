"""members + emergency contacts for T2 member entry

Revision ID: 002_members
Revises: 001_staff_accounts
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_members"
down_revision: Union[str, None] = "001_staff_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("personal_id", sa.String(64), nullable=False),
        sa.Column("rab_id", sa.String(32), nullable=False),
        sa.Column("rfid", sa.String(64), nullable=False),
        sa.Column("rank", sa.String(64), nullable=False),
        sa.Column("wing", sa.String(64), nullable=False),
        sa.Column("member_type", sa.String(16), nullable=False),
        sa.Column("dropdown_no", sa.String(64), nullable=False),
        sa.Column("phone", sa.String(64), nullable=False),
        sa.Column("status", sa.String(1), nullable=False),
        sa.Column("approval_status", sa.String(16), nullable=False),
        sa.Column("bank_name", sa.String(128), nullable=False),
        sa.Column("account_name", sa.String(128), nullable=False),
        sa.Column("account_number", sa.String(64), nullable=False),
        sa.Column("routing", sa.String(64), nullable=False),
        sa.Column("branch", sa.String(128), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("out_date", sa.Date(), nullable=True),
        sa.Column("documents", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("rab_id", name="uq_members_rab_id"),
    )
    op.create_table(
        "member_emergency_contacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("member_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False),
        sa.Column("phone", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
            name="fk_member_emergency_contacts_member_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_member_emergency_contacts_member_id",
        "member_emergency_contacts",
        ["member_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_member_emergency_contacts_member_id",
        table_name="member_emergency_contacts",
    )
    op.drop_table("member_emergency_contacts")
    op.drop_table("members")
