"""staff emails @mess.local → @mess.rab

Revision ID: 004_users_email_mess_rab
Revises: 003_users_email
Create Date: 2026-08-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_users_email_mess_rab"
down_revision: Union[str, None] = "003_users_email"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE users SET email = REPLACE(email, '@mess.local', '@mess.rab') "
            "WHERE email LIKE '%@mess.local'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE users SET email = REPLACE(email, '@mess.rab', '@mess.local') "
            "WHERE email LIKE '%@mess.rab'"
        )
    )
