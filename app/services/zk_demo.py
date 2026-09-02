"""Live ZKTeco pull for demo — no DB writes."""

from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from zk import ZK

from app.core.config import settings
from app.core.errors import ApiError


def assert_demo_enabled() -> None:
    if not settings.zk_demo_enabled:
        raise ApiError(
            code="ZK_DEMO_DISABLED",
            status=404,
            detail="ZK demo API is disabled.",
        )


def _iso(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep="T", timespec="seconds")
    return str(value)


def user_to_dict(user: Any) -> dict[str, Any]:
    return {
        "user_id": str(getattr(user, "user_id", "")),
        "name": (getattr(user, "name", None) or "").strip(),
        "privilege": getattr(user, "privilege", None),
        "group_id": str(getattr(user, "group_id", "") or ""),
        "card": str(getattr(user, "card", "") or ""),
    }


def attendance_to_dict(row: Any) -> dict[str, Any]:
    return {
        "user_id": str(getattr(row, "user_id", "")),
        "punched_at": _iso(getattr(row, "timestamp", None)),
        "status": getattr(row, "status", None),
        "punch": getattr(row, "punch", None),
        "uid": getattr(row, "uid", None),
    }


@contextmanager
def zk_connection() -> Iterator[Any]:
    client = ZK(
        settings.zk_host,
        port=settings.zk_port,
        timeout=settings.zk_timeout,
        password=settings.zk_password,
    )
    conn = None
    try:
        conn = client.connect()
        yield conn
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(
            code="ZK_UNREACHABLE",
            status=503,
            detail=f"Could not reach ZK device: {e}",
        ) from e
    finally:
        if conn is not None:
            try:
                conn.disconnect()
            except Exception:
                pass


def check_reachable() -> dict[str, Any]:
    assert_demo_enabled()
    started = time.perf_counter()
    try:
        with zk_connection():
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "reachable": True,
                "host": settings.zk_host,
                "port": settings.zk_port,
                "latency_ms": latency_ms,
            }
    except ApiError as e:
        if e.code == "ZK_UNREACHABLE":
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "reachable": False,
                "host": settings.zk_host,
                "port": settings.zk_port,
                "latency_ms": latency_ms,
                "error": e.detail,
            }
        raise


def fetch_users() -> list[dict[str, Any]]:
    assert_demo_enabled()
    with zk_connection() as conn:
        try:
            users = conn.get_users() or []
        except Exception as e:
            raise ApiError(
                code="ZK_UNREACHABLE",
                status=503,
                detail=f"Could not pull ZK users: {e}",
            ) from e
        rows = [user_to_dict(u) for u in users]
    rows.sort(key=lambda r: (r["name"].lower(), r["user_id"]))
    return rows


def fetch_attendance(
    *,
    limit: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    assert_demo_enabled()
    with zk_connection() as conn:
        try:
            logs = conn.get_attendance() or []
        except Exception as e:
            raise ApiError(
                code="ZK_UNREACHABLE",
                status=503,
                detail=f"Could not pull ZK attendance: {e}",
            ) from e
        rows = [attendance_to_dict(r) for r in logs]
    if from_date or to_date:
        lo = from_date or "0000-01-01"
        hi = to_date or "9999-12-31"
        rows = [
            r
            for r in rows
            if r["punched_at"] and lo <= r["punched_at"][:10] <= hi
        ]
    rows.sort(key=lambda r: r["punched_at"] or "", reverse=True)
    if limit is not None and limit >= 0:
        return rows[:limit]
    return rows
