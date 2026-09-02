import pytest
from tests.conftest import SEED_PASSWORD
from tests.test_login import assert_ok, assert_problem, login
from app.db.session import SessionLocal
from app.models.member import Member, MemberEmergencyContact


@pytest.fixture(autouse=True)
def clean_members(create_schema):
    db = SessionLocal()
    db.query(MemberEmergencyContact).delete()
    db.query(Member).delete()
    db.commit()
    db.close()
    yield


def register(client, **fields):
    payload = {"name": "Test Member", "rab_id": "RAB-ENTRY-1", **fields}
    return client.post("/api/v1/public/register", json=payload)


def test_t2_1_empty_name(client):
    res = register(client, name="", rab_id="RAB-T21")
    body = assert_problem(res, status=422, code="VALIDATION_ERROR")
    assert body["errors"]
    assert any(e["field"] == "name" for e in body["errors"])


def test_t2_2_empty_rab_id(client):
    res = register(client, name="Someone", rab_id="")
    body = assert_problem(res, status=422, code="VALIDATION_ERROR")
    assert body["errors"]
    assert any(e["field"] == "rab_id" for e in body["errors"])


def test_t2_3_valid_pending_inactive(client):
    res = register(
        client,
        name="Entry One",
        rab_id="RAB-T23",
        status="1",
        approval_status="approved",
        created_via="cc_staff",
        password="should-ignore",
    )
    body = assert_ok(res, status=201)
    data = body["data"]
    assert data["name"] == "Entry One"
    assert data["rab_id"] == "RAB-T23"
    assert data["approval_status"] == "pending_cc"
    assert data["status"] == "0"
    assert data["created_via"] == "public_register"
    assert "password" not in data
    assert "password_hash" not in data


def test_m1_public_register_pending_cc(client):
    """MEMBER_APPROVAL_PLAN M1 — server forces CC queue + inactive."""
    res = register(client, name="Queue Me", rab_id="RAB-M1")
    body = assert_ok(res, status=201)
    data = body["data"]
    assert data["approval_status"] == "pending_cc"
    assert data["status"] == "0"
    assert data["created_via"] == "public_register"


def test_t2_4_duplicate_rab_id(client):
    first = register(client, rab_id="RAB-T24")
    assert_ok(first, status=201)
    second = register(client, name="Other", rab_id="RAB-T24")
    assert_problem(second, status=409, code="CONFLICT_RAB_ID")


def test_t2_5_rab_id_case_fold(client):
    first = register(client, rab_id="rab-1")
    assert_ok(first, status=201)
    assert first.json()["data"]["rab_id"] == "RAB-1"
    second = register(client, name="Clone", rab_id="RAB-1")
    assert_problem(second, status=409, code="CONFLICT_RAB_ID")


def test_t2_6_does_not_create_staff(client, seed_staff):
    from app.models.staff import StaffAccount

    db = SessionLocal()
    before = db.query(StaffAccount).count()
    db.close()
    assert_ok(register(client, rab_id="RAB-T26"), status=201)
    db = SessionLocal()
    after = db.query(StaffAccount).count()
    db.close()
    assert after == before


def test_t2_7_member_cannot_staff_login(client, seed_staff):
    assert_ok(register(client, rab_id="RAB-T27"), status=201)
    res = login(client, email="rab-t27@mess.rab", password=SEED_PASSWORD)
    assert_problem(res, status=401, code="AUTH_INVALID_CREDENTIALS")
