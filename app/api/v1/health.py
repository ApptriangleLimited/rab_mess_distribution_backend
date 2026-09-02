from fastapi import APIRouter

from app.db.session import ping_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    ping_db()
    return {"status": "ok"}
