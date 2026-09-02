"""Create mess_db + mess_db_test on the server from DATABASE_URL (no DB name).

Usage (from backend/):
  ./venv/bin/python scripts/setup_test_db.py
  ./venv/bin/alembic upgrade head
  DATABASE_URL=...mess_db_test... ./venv/bin/pytest -q
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.core.config import settings  # noqa: E402


def _server_url() -> str:
    url = make_url(settings.database_url)
    return url.set(database=None).render_as_string(hide_password=False)


def main() -> None:
    engine = create_engine(_server_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        for name in ("mess_db", "mess_db_test"):
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS {name} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            print(f"ok: {name}")


if __name__ == "__main__":
    main()
