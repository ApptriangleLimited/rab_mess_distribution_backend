"""daily cockpit tables: assignments, locks, carry suppress, boro khana, rates

Revision ID: 006_daily_cockpit
Revises: 005_member_approval_workflow
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_daily_cockpit"
down_revision: Union[str, None] = "005_member_approval_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BUILTIN_RATES: tuple[tuple[str, str, bool], ...] = (
    ("FR", "220.00", True),
    ("CL", "0.00", True),
    ("PL", "0.00", True),
    ("WR", "0.00", True),
    ("CD", "0.00", True),
    ("WIT", "0.00", True),
    ("MED", "0.00", True),
    ("TRG", "0.00", True),
    ("MS", "180.00", True),
    ("FUEL", "50.00", True),
    ("CLFR", "2500.00", True),
)


def upgrade() -> None:
    op.create_table(
        "allowance_rates",
        sa.Column("tag", sa.String(16), primary_key=True),
        sa.Column("amount_per_day", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "daily_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("member_id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tag", sa.String(16), nullable=False),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
            name="fk_daily_assignments_member_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            name="fk_daily_assignments_updated_by",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("member_id", "date", name="uq_daily_assignments_member_date"),
    )
    op.create_index("ix_daily_assignments_date", "daily_assignments", ["date"])
    op.create_index(
        "ix_daily_assignments_member_date",
        "daily_assignments",
        ["member_id", "date"],
    )
    op.create_index(
        "ix_daily_assignments_date_tag",
        "daily_assignments",
        ["date", "tag"],
    )

    op.create_table(
        "approved_dates",
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("approved_by", sa.String(36), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
            name="fk_approved_dates_approved_by",
            ondelete="SET NULL",
        ),
    )

    op.create_table(
        "suppressed_carries",
        sa.Column("member_id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
            name="fk_suppressed_carries_member_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("member_id", "date", name="pk_suppressed_carries"),
    )
    op.create_index(
        "ix_suppressed_carries_date",
        "suppressed_carries",
        ["date"],
    )

    op.create_table(
        "boro_khana_dates",
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("set_by", sa.String(36), nullable=True),
        sa.Column("set_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["set_by"],
            ["users.id"],
            name="fk_boro_khana_dates_set_by",
            ondelete="SET NULL",
        ),
    )

    for tag, amount, is_builtin in _BUILTIN_RATES:
        op.execute(
            sa.text(
                "INSERT INTO allowance_rates (tag, amount_per_day, is_builtin) "
                "VALUES (:tag, :amount, :is_builtin)"
            ).bindparams(tag=tag, amount=amount, is_builtin=is_builtin)
        )


def downgrade() -> None:
    op.drop_table("boro_khana_dates")
    op.drop_index("ix_suppressed_carries_date", table_name="suppressed_carries")
    op.drop_table("suppressed_carries")
    op.drop_table("approved_dates")
    op.drop_index("ix_daily_assignments_date_tag", table_name="daily_assignments")
    op.drop_index("ix_daily_assignments_member_date", table_name="daily_assignments")
    op.drop_index("ix_daily_assignments_date", table_name="daily_assignments")
    op.drop_table("daily_assignments")
    op.drop_table("allowance_rates")
