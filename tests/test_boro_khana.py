from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.daily import BoroKhanaDate, DailyAssignment
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED, CREATED_VIA_DAILY
from app.services.carry import seed_builtin_rates
from tests.test_login import assert_ok, assert_problem, login

BK_DATE = "2026-08-24"


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
        name="BK Test",
        rab_id=rab_id,
        status="1",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def test_c8_put_toggles_without_touching_assignments(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-BK1")
    member_id = member.id
    db.add(
        DailyAssignment(
            member_id=member_id,
            date=date.fromisoformat(BK_DATE),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()
    db.close()

    on_res = client.put(
        f"/api/v1/boro-khana/{BK_DATE}",
        headers=_auth_headers(client),
        json={"on": True},
    )
    on_body = assert_ok(on_res)
    assert on_body["data"] == {"date": BK_DATE, "on": True}

    get_res = client.get(
        "/api/v1/boro-khana",
        headers=_auth_headers(client),
        params={"from": "2026-08-01", "to": "2026-08-31"},
    )
    assert BK_DATE in assert_ok(get_res)["data"]["dates"]

    assign_res = client.get(
        "/api/v1/assignments",
        headers=_auth_headers(client),
        params={"date": BK_DATE, "member_id": member_id},
    )
    assert assert_ok(assign_res)["data"]["items"][0]["tag"] == "MS"

    off_res = client.put(
        f"/api/v1/boro-khana/{BK_DATE}",
        headers=_auth_headers(client),
        json={"on": False},
    )
    assert assert_ok(off_res)["data"]["on"] is False


def test_cc_cannot_toggle_boro_khana(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    res = client.put(
        f"/api/v1/boro-khana/{BK_DATE}",
        headers=_auth_headers(client, email="cc@mess.rab"),
        json={"on": True},
    )
    assert_problem(res, status=403, code="AUTH_UNAUTHORIZED")


def test_put_boro_khana_idempotent(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    headers = _auth_headers(client)
    first = client.put(
        f"/api/v1/boro-khana/{BK_DATE}",
        headers=headers,
        json={"on": True},
    )
    second = client.put(
        f"/api/v1/boro-khana/{BK_DATE}",
        headers=headers,
        json={"on": True},
    )
    assert_ok(first)
    assert_ok(second)["data"]["on"] is True
    db = SessionLocal()
    count = db.query(BoroKhanaDate).filter(BoroKhanaDate.date == date.fromisoformat(BK_DATE)).count()
    db.close()
    assert count == 1
