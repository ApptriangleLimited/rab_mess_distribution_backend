from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.daily import ApprovedDate, DailyAssignment
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED, CREATED_VIA_DAILY
from app.services.carry import seed_builtin_rates
from tests.test_login import assert_ok, assert_problem, login

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
        name="Assignment API Test",
        rab_id=rab_id,
        status="1",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def test_c1_put_and_get_stored(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-A1")
    member_id = member.id
    db.close()

    put = client.put(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        json={"member_id": member_id, "date": FUTURE_DATE, "tag": "ms"},
    )
    body = assert_ok(put)
    item = body["data"]["items"][0]
    assert item["source"] == "stored"
    assert item["tag"] == "MS"

    get_res = client.get(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"date": FUTURE_DATE, "member_id": member_id},
    )
    get_body = assert_ok(get_res)
    assert get_body["data"]["items"][0]["source"] == "stored"
    assert get_body["data"]["items"][0]["tag"] == "MS"


def test_c2_clear_suppressed(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-A2")
    member_id = member.id
    db.add(
        DailyAssignment(
            member_id=member_id,
            date=date.fromisoformat(FUTURE_DATE),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()
    db.close()

    res = client.delete(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"member_id": member_id, "date": FUTURE_DATE},
    )
    body = assert_ok(res)
    assert body["data"]["items"][0]["source"] == "suppressed"

    get_res = client.get(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"date": FUTURE_DATE, "member_id": member_id},
    )
    get_body = assert_ok(get_res)
    assert get_body["data"]["items"][0]["source"] == "suppressed"


def test_c3_get_carry_from_prior(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-A3")
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

    get_res = client.get(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"date": FUTURE_DATE, "member_id": member_id},
    )
    body = assert_ok(get_res)
    assert body["data"]["items"][0]["source"] == "carry"
    assert body["data"]["items"][0]["tag"] == "FR"


def test_c4_edit_unlocks_locked_day(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-A4")
    member_id = member.id
    db.add(ApprovedDate(date=date.fromisoformat(FUTURE_DATE), approved_at=_utcnow()))
    db.commit()
    db.close()

    res = client.put(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        json={"member_id": member_id, "date": FUTURE_DATE, "tag": "MS"},
    )
    assert_ok(res)

    lock_res = client.get(
        f"/api/v1/days/{FUTURE_DATE}/lock",
        headers=_auth_headers(client),
    )
    assert assert_ok(lock_res)["data"]["locked"] is False


def test_cc_cannot_write_assignments(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-A5")
    member_id = member.id
    db.close()

    res = client.put(
        "/api/v1/assignments",
        headers=_auth_headers(client, email="cc@mess.rab"),
        json={"member_id": member_id, "date": FUTURE_DATE, "tag": "MS"},
    )
    assert_problem(res, status=403, code="AUTH_UNAUTHORIZED")


def test_bulk_and_range(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member_a = _insert_member(db, rab_id="RAB-A6A")
    member_b = _insert_member(db, rab_id="RAB-A6B")
    member_a_id = member_a.id
    member_b_id = member_b.id
    db.close()

    bulk = client.put(
        "/api/v1/assignments/bulk",
        headers=_auth_headers(client),
        json={
            "date": FUTURE_DATE,
            "tag": "CD",
            "member_ids": [member_a_id, member_b_id],
        },
    )
    bulk_body = assert_ok(bulk)
    assert bulk_body["data"]["updated"] == 2

    range_res = client.put(
        "/api/v1/assignments/range",
        headers=_auth_headers(client),
        json={
            "member_id": member_a_id,
            "dates": ["2026-08-26", "2026-08-27"],
            "tag": "MS",
        },
    )
    range_body = assert_ok(range_res)
    assert range_body["data"]["updated"] == 2
    assert all(item["tag"] == "MS" for item in range_body["data"]["items"])
