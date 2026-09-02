import pytest
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.db.session import engine, ping_db, ping_url


def test_wrong_url_fails_loud():
    with pytest.raises(RuntimeError, match="MySQL connect failed"):
        ping_url(
            "mysql+pymysql://no_such_user:bad@127.0.0.1:3306/mess_db_test"
            "?charset=utf8mb4"
        )


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mysql_connects():
    ping_db()
    url = make_url(settings.database_url)
    assert url.database == "mess_db_test"
    with engine.connect() as conn:
        current = conn.execute(text("SELECT DATABASE()")).scalar()
    assert current == "mess_db_test"
