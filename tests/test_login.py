from tests.conftest import SEED_PASSWORD


def assert_problem(response, *, status: int, code: str) -> dict:
    assert response.status_code == status
    assert "application/problem+json" in response.headers.get("content-type", "")
    body = response.json()
    assert body["ok"] is False
    assert body["code"] == code
    assert body["status"] == status
    assert "password_hash" not in str(body).lower()
    return body


def assert_ok(response, *, status: int = 200) -> dict:
    assert response.status_code == status
    body = response.json()
    assert body["ok"] is True
    assert "data" in body
    assert "meta" in body
    assert isinstance(body["meta"], dict)
    assert "password_hash" not in str(body).lower()
    return body


def login(client, email="daily@mess.rab", password=SEED_PASSWORD, **extra):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, **extra},
    )


def test_t1_1_unknown_user(client, seed_staff):
    res = login(client, email="no_such_desk@mess.rab")
    assert_problem(res, status=401, code="AUTH_INVALID_CREDENTIALS")


def test_t1_2_wrong_password(client, seed_staff):
    res = login(client, password="wrong-password")
    assert_problem(res, status=401, code="AUTH_INVALID_CREDENTIALS")


def test_t1_3_seeded_daily_ok(client, seed_staff):
    res = login(client)
    body = assert_ok(res)
    data = body["data"]
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str) and data["access_token"]
    assert data["expires_in"] == 3600
    assert data["staff"]["email"] == "daily@mess.rab"
    assert data["staff"]["role"] == "daily"
    assert data["staff"]["display_name"] == "Daily Desk"
    assert data["staff"]["id"] == seed_staff["daily"].id


def test_t1_4_role_in_body_ignored(client, seed_staff):
    res = login(client, role="admin")
    body = assert_ok(res)
    assert body["data"]["staff"]["role"] == "daily"


def test_t1_5_inactive_forbidden(client, seed_staff):
    res = login(client, email="inactive_desk@mess.rab")
    assert_problem(res, status=403, code="AUTH_INACTIVE")


def test_t1_6_me_no_token(client, seed_staff):
    res = client.get("/api/v1/auth/me")
    assert_problem(res, status=401, code="AUTH_UNAUTHORIZED")


def test_t1_7_me_valid_token(client, seed_staff):
    token = login(client).json()["data"]["access_token"]
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = assert_ok(res)
    assert body["data"]["email"] == "daily@mess.rab"
    assert body["data"]["role"] == "daily"
    assert body["data"]["display_name"] == "Daily Desk"
    assert body["data"]["id"] == seed_staff["daily"].id


def test_t1_8_tampered_jwt(client, seed_staff):
    token = login(client).json()["data"]["access_token"]
    tampered = token[:-4] + ("aaaa" if token[-4:] != "aaaa" else "bbbb")
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert_problem(res, status=401, code="AUTH_UNAUTHORIZED")


def test_logout_204_empty(client, seed_staff):
    token = login(client).json()["data"]["access_token"]
    res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 204
    assert res.content == b""
