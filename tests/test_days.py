from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.daily import ApprovedDate, DailyAssignment
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED, CREATED_VIA_DAILY
from app.services.carry import seed_builtin_rates
from tests.test_login import assert_ok, login

FUTURE_DATE = "2026-08-25"
PRIOR_DATE = "2026-08-24"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _auth_headers(client, email="daily@mess.rab"):
    token = login(client, email=email).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_rates(create_schema):
    db = SessionLocal()
    seed_builtin_rates(db)
    db.commit()
    db.close()


def _insert_member(db, *, rab_id: str) -> Member:
    db.query(Member).filter(Member.rab_id == rab_id).delete()
    member = Member(
        name="Day Lock Test",
        rab_id=rab_id,
        status="1",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def test_c5_approve_fills_carry_and_locks(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-D1")
    member_id = member.id
    db.add(
        DailyAssignment(
            member_id=member_id,
            date=date.fromisoformat(PRIOR_DATE),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()
    db.close()

    res = client.post(
        f"/api/v1/days/{FUTURE_DATE}/approve",
        headers=_auth_headers(client),
    )
    body = assert_ok(res)
    assert body["data"]["filled"] == 1
    assert body["data"]["locked"] is True

    lock_res = client.get(
        f"/api/v1/days/{FUTURE_DATE}/lock",
        headers=_auth_headers(client),
    )
    assert assert_ok(lock_res)["data"]["locked"] is True

    get_res = client.get(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"date": FUTURE_DATE, "member_id": member_id},
    )
    assert assert_ok(get_res)["data"]["items"][0]["source"] == "stored"


def test_approve_idempotent_when_already_locked(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-D2")
    db.add(ApprovedDate(date=date.fromisoformat(FUTURE_DATE), approved_at=_utcnow()))
    db.commit()
    db.close()

    res = client.post(
        f"/api/v1/days/{FUTURE_DATE}/approve",
        headers=_auth_headers(client),
    )
    body = assert_ok(res)
    assert body["data"]["filled"] == 0
    assert body["data"]["locked"] is True


def test_c6_edit_after_approve_unlocks_day(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-D3")
    member_id = member.id
    db.add(
        DailyAssignment(
            member_id=member_id,
            date=date.fromisoformat(PRIOR_DATE),
            tag="FR",
            updated_at=_utcnow(),
        )
    )
    db.commit()
    db.close()

    client.post(
        f"/api/v1/days/{FUTURE_DATE}/approve",
        headers=_auth_headers(client),
    )

    put = client.put(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        json={"member_id": member_id, "date": FUTURE_DATE, "tag": "CD"},
    )
    assert_ok(put)

    lock_res = client.get(
        f"/api/v1/days/{FUTURE_DATE}/lock",
        headers=_auth_headers(client),
    )
    assert assert_ok(lock_res)["data"]["locked"] is False


def test_list_day_locks(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    db.add(ApprovedDate(date=date.fromisoformat("2026-08-20"), approved_at=_utcnow()))
    db.add(ApprovedDate(date=date.fromisoformat("2026-08-22"), approved_at=_utcnow()))
    db.commit()
    db.close()

    res = client.get(
        "/api/v1/days/locks",
        headers=_auth_headers(client),
        params={"from": "2026-08-01", "to": "2026-08-31"},
    )
    body = assert_ok(res)
    assert body["data"]["dates"] == ["2026-08-20", "2026-08-22"]
