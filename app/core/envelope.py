from typing import Any

from fastapi.responses import JSONResponse


def ok(
    data: dict[str, Any],
    *,
    status: int = 200,
    meta: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"ok": True, "data": data, "meta": meta or {}},
        headers=headers,
    )
