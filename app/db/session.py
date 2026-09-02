from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ping_url(database_url: str) -> None:
    url = make_url(database_url)
    safe = f"{url.host}:{url.port or 3306}/{url.database}"
    probe = create_engine(database_url, pool_pre_ping=True)
    try:
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(
            f"MySQL connect failed ({safe}). "
            f"Check DATABASE_URL / TEST_DATABASE_URL (see .env.example). {exc}"
        ) from None
    finally:
        probe.dispose()


def ping_db() -> None:
    ping_url(settings.database_url)
