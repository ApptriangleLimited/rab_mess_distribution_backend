"""ZKTeco demo API — live pull, no persistence."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.deps import get_optional_staff
from app.core.envelope import ok
from app.core.errors import ApiError
from app.models.staff import StaffAccount
from app.services import zk_demo

router = APIRouter(prefix="/api/v1/zk/demo", tags=["zk-demo"])


def require_zk_demo_access(
    staff: StaffAccount | None = Depends(get_optional_staff),
) -> StaffAccount | None:
    zk_demo.assert_demo_enabled()
    if settings.zk_demo_anonymous:
        return staff
    if staff is None:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=401,
            detail="Missing or invalid token.",
        )
    return staff


@router.get("/status")
def zk_demo_status(_auth: StaffAccount | None = Depends(require_zk_demo_access)):
    data = zk_demo.check_reachable()
    return ok(data)


@router.get("/users")
def zk_demo_users(_auth: StaffAccount | None = Depends(require_zk_demo_access)):
    items = zk_demo.fetch_users()
    return ok({"items": items, "total": len(items)})


@router.get("/attendance")
def zk_demo_attendance(
    limit: int | None = Query(
        None,
        ge=1,
        le=50000,
        description="Max punches after date filter (newest first). Default: all in range.",
    ),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    _auth: StaffAccount | None = Depends(require_zk_demo_access),
):
    items = zk_demo.fetch_attendance(
        limit=limit,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
    )
    return ok(
        {
            "items": items,
            "total": len(items),
            "limit": limit,
            "from": from_date.isoformat() if from_date else None,
            "to": to_date.isoformat() if to_date else None,
        }
    )
