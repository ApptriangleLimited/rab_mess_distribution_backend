from app.db.session import SessionLocal
from app.models.member import Member
from app.models.member_constants import (
    APPROVAL_PENDING_CC,
    APPROVAL_PENDING_DAILY,
    CREATED_VIA_PUBLIC,
)
from tests.test_login import assert_ok, assert_problem, login


def _auth_headers(client, email="daily@mess.rab"):
    token = login(client, email=email).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _insert_member(
    *,
    rab_id: str,
    approval_status: str,
    status: str = "0",
    created_via: str = CREATED_VIA_PUBLIC,
) -> str:
    db = SessionLocal()
    db.query(Member).filter(Member.rab_id == rab_id).delete()
    member = Member(
        name="Transition Test",
        rab_id=rab_id,
        status=status,
        approval_status=approval_status,
        created_via=created_via,
    )
    db.add(member)
    db.commit()
    member_id = member.id
    db.close()
    return member_id


def test_m2_cc_cannot_daily_approve_pending_cc(client, seed_staff, create_schema):
    member_id = _insert_member(
        rab_id="RAB-M2",
        approval_status=APPROVAL_PENDING_CC,
    )
    res = client.post(
        f"/api/v1/members/{member_id}/approve",
        headers=_auth_headers(client, email="cc@mess.rab"),
    )
    assert_problem(res, status=403, code="AUTH_UNAUTHORIZED")


def test_m3_cc_accept_to_pending_daily(client, seed_staff, create_schema):
    member_id = _insert_member(
        rab_id="RAB-M3",
        approval_status=APPROVAL_PENDING_CC,
    )
    res = client.post(
        f"/api/v1/members/{member_id}/cc-accept",
        headers=_auth_headers(client, email="cc@mess.rab"),
    )
    body = assert_ok(res)
    data = body["data"]
    assert data["approval_status"] == "pending_daily"
    assert data["status"] == "0"


def test_m4_daily_approve_active(client, seed_staff, create_schema):
    member_id = _insert_member(
        rab_id="RAB-M4",
        approval_status=APPROVAL_PENDING_DAILY,
    )
    res = client.post(
        f"/api/v1/members/{member_id}/approve",
        headers=_auth_headers(client, email="daily@mess.rab"),
    )
    body = assert_ok(res)
    data = body["data"]
    assert data["approval_status"] == "approved"
    assert data["status"] == "1"


def test_m7_cc_and_daily_reject(client, seed_staff, create_schema):
    cc_member_id = _insert_member(
        rab_id="RAB-M7A",
        approval_status=APPROVAL_PENDING_CC,
    )
    res_cc = client.post(
        f"/api/v1/members/{cc_member_id}/cc-reject",
        headers=_auth_headers(client, email="cc@mess.rab"),
    )
    assert assert_ok(res_cc)["data"]["approval_status"] == "rejected"

    daily_member_id = _insert_member(
        rab_id="RAB-M7B",
        approval_status=APPROVAL_PENDING_DAILY,
    )
    res_daily = client.post(
        f"/api/v1/members/{daily_member_id}/reject",
        headers=_auth_headers(client, email="daily@mess.rab"),
    )
    assert assert_ok(res_daily)["data"]["approval_status"] == "rejected"


def test_daily_cannot_cc_accept(client, seed_staff, create_schema):
    member_id = _insert_member(
        rab_id="RAB-ROLE-1",
        approval_status=APPROVAL_PENDING_CC,
    )
    res = client.post(
        f"/api/v1/members/{member_id}/cc-accept",
        headers=_auth_headers(client, email="daily@mess.rab"),
    )
    assert_problem(res, status=403, code="AUTH_UNAUTHORIZED")


def test_wrong_stage_cc_accept_returns_422(client, seed_staff, create_schema):
    member_id = _insert_member(
        rab_id="RAB-STAGE-1",
        approval_status=APPROVAL_PENDING_DAILY,
    )
    res = client.post(
        f"/api/v1/members/{member_id}/cc-accept",
        headers=_auth_headers(client, email="cc@mess.rab"),
    )
    assert_problem(res, status=422, code="VALIDATION_ERROR")


def test_member_not_found(client, seed_staff, create_schema):
    res = client.post(
        "/api/v1/members/00000000-0000-0000-0000-000000000099/cc-accept",
        headers=_auth_headers(client, email="cc@mess.rab"),
    )
    assert_problem(res, status=404, code="VALIDATION_ERROR")
