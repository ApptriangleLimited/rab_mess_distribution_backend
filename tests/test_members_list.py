from tests.conftest import SEED_PASSWORD
from tests.test_login import assert_ok, assert_problem, login
from app.db.session import SessionLocal
from app.models.member import Member


def _auth_headers(client):
    token = login(client).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_members_list_unauthorized(client, seed_staff):
    res = client.get("/api/v1/members")
    assert_problem(res, status=401, code="AUTH_UNAUTHORIZED")


def test_members_list_ok(client, seed_staff, create_schema):
    db = SessionLocal()
    db.query(Member).delete()
    db.add(
        Member(
            name="List One",
            rab_id="RAB-LIST-1",
            status="1",
            approval_status="approved",
            created_via="cc_staff",
            member_type="permanent",
            rank="SI",
            wing="HQ",
        )
    )
    db.add(
        Member(
            name="List Two",
            rab_id="RAB-LIST-2",
            status="0",
            approval_status="pending_daily",
            created_via="cc_staff",
            member_type="new",
        )
    )
    db.commit()
    db.close()

    res = client.get("/api/v1/members", headers=_auth_headers(client))
    body = assert_ok(res)
    data = body["data"]
    assert data["total"] >= 2
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert isinstance(data["items"], list)
    ids = {m["rab_id"] for m in data["items"]}
    assert "RAB-LIST-1" in ids
    assert "RAB-LIST-2" in ids
    one = next(m for m in data["items"] if m["rab_id"] == "RAB-LIST-1")
    assert one["approval_status"] == "approved"
    assert "password_hash" not in str(body).lower()


def test_members_list_honors_page_size(client, seed_staff, create_schema):
    db = SessionLocal()
    db.query(Member).delete()
    for i in range(30):
        db.add(
            Member(
                name=f"Page {i}",
                rab_id=f"RAB-PAGE-{i:03d}",
                status="1",
                approval_status="approved",
                member_type="permanent",
            )
        )
    db.commit()
    db.close()

    headers = _auth_headers(client)

    # No page_size → default 25
    res = client.get("/api/v1/members", headers=headers)
    body = assert_ok(res)
    assert body["data"]["page_size"] == 25
    assert len(body["data"]["items"]) == 25
    assert body["data"]["total"] == 30

    # FE per-page wins
    res2 = client.get(
        "/api/v1/members",
        params={"page": 1, "page_size": 10},
        headers=headers,
    )
    body2 = assert_ok(res2)
    assert body2["data"]["page_size"] == 10
    assert len(body2["data"]["items"]) == 10
    assert body2["data"]["total"] == 30

    res3 = client.get(
        "/api/v1/members",
        params={"page": 2, "page_size": 10},
        headers=headers,
    )
    body3 = assert_ok(res3)
    assert body3["data"]["page"] == 2
    assert len(body3["data"]["items"]) == 10
    ids_p1 = {m["rab_id"] for m in body2["data"]["items"]}
    ids_p2 = {m["rab_id"] for m in body3["data"]["items"]}
    assert ids_p1.isdisjoint(ids_p2)
    db = SessionLocal()
    db.query(Member).delete()
    db.add(
        Member(name="Pend", rab_id="RAB-PEND", status="0", approval_status="pending_daily", created_via="cc_staff")
    )
    db.add(
        Member(name="Ok", rab_id="RAB-OK", status="1", approval_status="accepted", created_via="cc_staff")
    )
    db.commit()
    db.close()

    res = client.get(
        "/api/v1/members",
        params={"approval": "pending_daily"},
        headers=_auth_headers(client),
    )
    body = assert_ok(res)
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["rab_id"] == "RAB-PEND"

    res2 = client.get(
        "/api/v1/members",
        params={"approval": "approved"},
        headers=_auth_headers(client),
    )
    body2 = assert_ok(res2)
    assert body2["data"]["total"] == 1
    assert body2["data"]["items"][0]["approval_status"] == "approved"
