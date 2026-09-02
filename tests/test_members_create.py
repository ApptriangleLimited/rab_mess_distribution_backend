from tests.test_login import assert_ok, assert_problem, login
from app.db.session import SessionLocal
from app.models.member import Member


def _auth_headers(client, email="daily@mess.rab"):
    token = login(client, email=email).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_member_unauthorized(client, seed_staff):
    res = client.post(
        "/api/v1/members",
        json={"name": "No Auth", "rab_id": "RAB-NOAUTH"},
    )
    assert_problem(res, status=401, code="AUTH_UNAUTHORIZED")


def test_m5_cc_create_pending_daily(client, seed_staff, create_schema):
    """MEMBER_APPROVAL_PLAN M5 — CC create → Daily queue, inactive."""
    db = SessionLocal()
    db.query(Member).filter(Member.rab_id == "RAB-CC-1").delete()
    db.commit()
    db.close()

    res = client.post(
        "/api/v1/members",
        headers=_auth_headers(client, email="cc@mess.rab"),
        json={
            "name": "CC Created",
            "rab_id": "RAB-CC-1",
            "status": "1",
            "approval_status": "approved",
            "phone": "01700000000",
        },
    )
    body = assert_ok(res, status=201)
    data = body["data"]
    assert data["name"] == "CC Created"
    assert data["rab_id"] == "RAB-CC-1"
    assert data["status"] == "0"
    assert data["approval_status"] == "pending_daily"
    assert data["created_via"] == "cc_staff"
    assert res.headers.get("location") == f"/api/v1/members/{data['id']}"


def test_m6_daily_create_approved(client, seed_staff, create_schema):
    """MEMBER_APPROVAL_PLAN M6 — Daily create → approved + active."""
    db = SessionLocal()
    db.query(Member).filter(Member.rab_id == "RAB-DAILY-1").delete()
    db.commit()
    db.close()

    res = client.post(
        "/api/v1/members",
        headers=_auth_headers(client, email="daily@mess.rab"),
        json={
            "name": "Daily Created",
            "rab_id": "RAB-DAILY-1",
            "status": "0",
            "approval_status": "pending_daily",
            "phone": "01700000001",
        },
    )
    body = assert_ok(res, status=201)
    data = body["data"]
    assert data["status"] == "1"
    assert data["approval_status"] == "approved"
    assert data["created_via"] == "daily_staff"


def test_create_member_duplicate(client, seed_staff, create_schema):
    headers = _auth_headers(client, email="cc@mess.rab")
    first = client.post(
        "/api/v1/members",
        headers=headers,
        json={"name": "One", "rab_id": "RAB-DUP-CC"},
    )
    assert_ok(first, status=201)
    second = client.post(
        "/api/v1/members",
        headers=headers,
        json={"name": "Two", "rab_id": "RAB-DUP-CC"},
    )
    assert_problem(second, status=409, code="CONFLICT_RAB_ID")
