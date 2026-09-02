from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.daily import BoroKhanaDate, DailyAssignment
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED, CREATED_VIA_DAILY
from app.services.carry import seed_builtin_rates
from tests.test_login import assert_ok, login

DAY_A = "2026-08-20"
DAY_B = "2026-08-21"
BK_DAY = "2026-08-24"


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


def _insert_member(db, *, rab_id: str, name: str = "Mess Test") -> Member:
    db.query(Member).filter(Member.rab_id == rab_id).delete()
    member = Member(
        name=name,
        rab_id=rab_id,
        status="1",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def test_d1_normal_day_only_explicit_ms(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-ME1")
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=date.fromisoformat(DAY_A),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()
    db.close()

    res = client.get(
        "/api/v1/mess/eaters",
        headers=_auth_headers(client),
        params={"date": DAY_B},
    )
    body = assert_ok(res)
    assert body["data"]["boro_khana"] is False
    assert body["data"]["total"] == 0

    res_a = client.get(
        "/api/v1/mess/eaters",
        headers=_auth_headers(client),
        params={"date": DAY_A},
    )
    body_a = assert_ok(res_a)
    assert body_a["data"]["total"] == 1
    assert body_a["data"]["items"][0]["mess_reason"] == "MS"
    assert body_a["data"]["items"][0]["rab_id"] == "RAB-ME1"


def test_d3_boro_khana_all_eaters_with_reasons(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    ms_member = _insert_member(db, rab_id="RAB-ME2", name="MS Guest")
    fr_member = _insert_member(db, rab_id="RAB-ME3", name="FR Guest")
    guest = _insert_member(db, rab_id="RAB-ME4", name="BK Guest")
    db.add(
        DailyAssignment(
            member_id=ms_member.id,
            date=date.fromisoformat(BK_DAY),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.add(
        DailyAssignment(
            member_id=fr_member.id,
            date=date.fromisoformat(BK_DAY),
            tag="FR",
            updated_at=_utcnow(),
        )
    )
    db.add(BoroKhanaDate(date=date.fromisoformat(BK_DAY), set_at=_utcnow()))
    db.commit()
    db.close()

    res = client.get(
        "/api/v1/mess/eaters",
        headers=_auth_headers(client),
        params={"date": BK_DAY},
    )
    body = assert_ok(res)
    assert body["data"]["boro_khana"] is True
    assert body["data"]["total"] == 3
    reasons = {item["rab_id"]: item["mess_reason"] for item in body["data"]["items"]}
    assert reasons["RAB-ME2"] == "MS"
    assert reasons["RAB-ME3"] == "FR"
    assert reasons["RAB-ME4"] == "BK"


def test_d2_ledger_ms_cd_with_carry_and_bk_days(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-ME5")
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=date.fromisoformat(DAY_A),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=date.fromisoformat(DAY_B),
            tag="CD",
            updated_at=_utcnow(),
        )
    )
    db.add(BoroKhanaDate(date=date.fromisoformat(BK_DAY), set_at=_utcnow()))
    db.commit()
    db.close()

    res = client.get(
        "/api/v1/mess/ledger",
        headers=_auth_headers(client),
        params={"from": "2026-08-20", "to": "2026-08-24"},
    )
    body = assert_ok(res)
    assert body["data"]["tag_codes"] == ["MS", "CD"]
    assert body["data"]["dates"] == [
        "2026-08-20",
        "2026-08-21",
        "2026-08-22",
        "2026-08-23",
        "2026-08-24",
    ]
    row = body["data"]["rows"][0]
    assert row["days"] == ["MS", "CD", "CD", "CD", "CD"]
    assert row["tag_counts"] == {"MS": 1, "CD": 4}
    bk = {item["date"]: item["eater_count"] for item in body["data"]["boro_khana_days"]}
    assert bk[BK_DAY] == 1
