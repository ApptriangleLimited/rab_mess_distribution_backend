"""Force mess_db_test before app import. Never run pytest against mess_db."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_DEFAULT_TEST_URL = (
    "mysql+pymysql://mess:mess_dev@127.0.0.1:3306/mess_db_test?charset=utf8mb4"
)

SEED_PASSWORD = "ChangeMe!"


def _test_database_url() -> str:
    raw = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not raw:
        raw = _DEFAULT_TEST_URL
    url = make_url(raw)
    if url.database != "mess_db_test":
        url = url.set(database="mess_db_test")
    return url.render_as_string(hide_password=False)


os.environ["DATABASE_URL"] = _test_database_url()

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import Base
from app.models.daily import (
    ApprovedDate,
    BoroKhanaDate,
    DailyAssignment,
    SuppressedCarry,
)
from app.models.member import Member, MemberEmergencyContact
from app.models.sender import SenderAccount, SenderTagMap
from app.models.staff import StaffAccount


@pytest.fixture(scope="session")
def create_schema() -> Iterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_cockpit_data(create_schema) -> Iterator[None]:
    db = SessionLocal()
    db.query(DailyAssignment).delete()
    db.query(SuppressedCarry).delete()
    db.query(ApprovedDate).delete()
    db.query(BoroKhanaDate).delete()
    db.query(SenderTagMap).delete()
    db.query(SenderAccount).delete()
    db.query(MemberEmergencyContact).delete()
    db.query(Member).delete()
    db.commit()
    db.close()
    yield


@pytest.fixture
def seed_staff(create_schema) -> Iterator[dict[str, StaffAccount]]:
    db = SessionLocal()
    db.query(StaffAccount).delete()
    db.commit()
    daily = StaffAccount(
        email="daily@mess.rab",
        password_hash=hash_password(SEED_PASSWORD),
        display_name="Daily Desk",
        role="daily",
        is_active=True,
    )
    cc = StaffAccount(
        email="cc@mess.rab",
        password_hash=hash_password(SEED_PASSWORD),
        display_name="CC Desk",
        role="cc",
        is_active=True,
    )
    inactive = StaffAccount(
        email="inactive_desk@mess.rab",
        password_hash=hash_password(SEED_PASSWORD),
        display_name="Inactive Desk",
        role="daily",
        is_active=False,
    )
    ration = StaffAccount(
        email="ration@mess.rab",
        password_hash=hash_password(SEED_PASSWORD),
        display_name="Ration Desk",
        role="ration",
        is_active=True,
    )
    db.add_all([daily, cc, inactive, ration])
    db.commit()
    db.refresh(daily)
    db.refresh(cc)
    db.refresh(inactive)
    db.refresh(ration)
    try:
        yield {"daily": daily, "cc": cc, "inactive": inactive, "ration": ration}
    finally:
        db.query(StaffAccount).delete()
        db.commit()
        db.close()
