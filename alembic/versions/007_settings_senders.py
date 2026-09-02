"""Settings senders + allowance rates tables.

Revision ID: 007_settings_senders
Revises: 006_daily_cockpit
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_settings_senders"
down_revision: Union[str, None] = "006_daily_cockpit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_SENDERS: tuple[tuple[str, str, str, str, str, str, str, tuple[str, ...]], ...] = (
    (
        "s_fr",
        "FR Pool",
        "Bangladesh Bank",
        "RAB FR Allowance",
        "9001001001",
        "000000001",
        "Head Office",
        ("FR",),
    ),
    (
        "s_ms",
        "Mess Fund",
        "Sonali Bank",
        "RAB Mess Fund",
        "9001001002",
        "000000002",
        "HQ Branch",
        ("MS",),
    ),
    (
        "s_ops",
        "Ops Contingency",
        "Agrani Bank",
        "RAB Ops Pool",
        "9001001003",
        "000000003",
        "Central",
        ("CD", "TRG"),
    ),
    (
        "s_med",
        "Medical Pool",
        "Janata Bank",
        "RAB Medical Fund",
        "9001001004",
        "000000004",
        "HQ Branch",
        ("MED", "WIT"),
    ),
    (
        "s_leave",
        "Leave / Admin",
        "Pubali Bank",
        "RAB Admin Pool",
        "9001001005",
        "000000005",
        "Banani",
        ("CL", "PL", "WR"),
    ),
)


def upgrade() -> None:
    op.create_table(
        "sender_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("bank_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("account_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("account_number", sa.String(64), nullable=False, server_default=""),
        sa.Column("routing", sa.String(32), nullable=False, server_default=""),
        sa.Column("branch", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "sender_tag_map",
        sa.Column("sender_id", sa.String(36), nullable=False),
        sa.Column("tag", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["sender_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("sender_id", "tag"),
        sa.UniqueConstraint("sender_id", "tag", name="uq_sender_tag_map_sender_tag"),
    )

    sender_table = sa.table(
        "sender_accounts",
        sa.column("id", sa.String),
        sa.column("label", sa.String),
        sa.column("bank_name", sa.String),
        sa.column("account_name", sa.String),
        sa.column("account_number", sa.String),
        sa.column("routing", sa.String),
        sa.column("branch", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    tag_table = sa.table(
        "sender_tag_map",
        sa.column("sender_id", sa.String),
        sa.column("tag", sa.String),
    )
    now = sa.func.now()
    for (
        sender_id,
        label,
        bank_name,
        account_name,
        account_number,
        routing,
        branch,
        tags,
    ) in _SEED_SENDERS:
        op.execute(
            sender_table.insert().values(
                id=sender_id,
                label=label,
                bank_name=bank_name,
                account_name=account_name,
                account_number=account_number,
                routing=routing,
                branch=branch,
                created_at=now,
                updated_at=now,
            )
        )
        for tag in tags:
            op.execute(
                tag_table.insert().values(sender_id=sender_id, tag=tag)
            )


def downgrade() -> None:
    op.drop_table("sender_tag_map")
    op.drop_table("sender_accounts")
