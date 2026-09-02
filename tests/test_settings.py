from app.db.session import SessionLocal
from app.models.sender import SenderAccount, SenderTagMap
from app.services.carry import seed_builtin_rates
from tests.test_login import assert_ok, assert_problem, login

CUSTOM_TAG = "OPS"


def _auth_headers(client, email="ration@mess.rab"):
    token = login(client, email=email).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_rates(create_schema):
    db = SessionLocal()
    seed_builtin_rates(db)
    db.commit()
    db.close()


def test_e1_get_and_put_rates(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    get_res = client.get(
        "/api/v1/settings/rates",
        headers=_auth_headers(client, email="daily@mess.rab"),
    )
    body = assert_ok(get_res)
    tags = {item["tag"] for item in body["data"]["items"]}
    assert "MS" in tags
    assert "FUEL" in tags

    put_res = client.put(
        "/api/v1/settings/rates",
        headers=_auth_headers(client),
        json={
            "items": [
                {"tag": "MS", "amount_per_day": 190},
                {"tag": "FUEL", "amount_per_day": 55},
            ]
        },
    )
    put_body = assert_ok(put_res)
    ms = next(item for item in put_body["data"]["items"] if item["tag"] == "MS")
    assert ms["amount_per_day"] == 190.0


def test_e1_add_and_delete_custom_rate(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    create_res = client.post(
        "/api/v1/settings/rates",
        headers=_auth_headers(client),
        json={"tag": CUSTOM_TAG, "amount_per_day": 99},
    )
    assert assert_ok(create_res, status=201)["data"]["tag"] == CUSTOM_TAG

    delete_res = client.delete(
        f"/api/v1/settings/rates/{CUSTOM_TAG}",
        headers=_auth_headers(client),
    )
    assert_ok(delete_res)

    blocked = client.delete(
        "/api/v1/settings/rates/MS",
        headers=_auth_headers(client),
    )
    assert_problem(blocked, status=422, code="VALIDATION_ERROR")


def test_e2_senders_crud(client, seed_staff, create_schema):
    _seed_rates(create_schema)
    list_res = client.get(
        "/api/v1/senders",
        headers=_auth_headers(client, email="daily@mess.rab"),
    )
    assert len(assert_ok(list_res)["data"]["items"]) >= 0

    create_res = client.post(
        "/api/v1/senders",
        headers=_auth_headers(client),
        json={
            "label": "Test Pool",
            "bank_name": "Test Bank",
            "account_name": "RAB Test",
            "account_number": "123",
            "routing": "999",
            "branch": "Test",
            "mapped_tags": ["MS", "CD"],
        },
    )
    created = assert_ok(create_res, status=201)["data"]
    sender_id = created["id"]
    assert created["mapped_tags"] == ["CD", "MS"]

    update_res = client.put(
        f"/api/v1/senders/{sender_id}",
        headers=_auth_headers(client),
        json={
            "label": "Updated Pool",
            "bank_name": "Test Bank",
            "account_name": "RAB Test",
            "account_number": "123",
            "routing": "999",
            "branch": "Test",
            "mapped_tags": ["FR"],
        },
    )
    updated = assert_ok(update_res)["data"]
    assert updated["label"] == "Updated Pool"
    assert updated["mapped_tags"] == ["FR"]

    delete_res = client.delete(
        f"/api/v1/senders/{sender_id}",
        headers=_auth_headers(client),
    )
    assert_ok(delete_res)
