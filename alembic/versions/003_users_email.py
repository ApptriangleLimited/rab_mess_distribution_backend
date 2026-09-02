"""users.username → users.email

Revision ID: 003_users_email
Revises: 002_members
Create Date: 2026-08-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_users_email"
down_revision: Union[str, None] = "002_members"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.alter_column(
        "users",
        "username",
        new_column_name="email",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    op.execute(
        sa.text(
            "UPDATE users SET email = CONCAT(LOWER(email), '@mess.local') "
            "WHERE email NOT LIKE '%@%'"
        )
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.execute(
        sa.text(
            "UPDATE users SET email = SUBSTRING_INDEX(email, '@', 1) "
            "WHERE email LIKE '%@mess.local'"
        )
    )
    op.alter_column(
        "users",
        "email",
        new_column_name="username",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])
