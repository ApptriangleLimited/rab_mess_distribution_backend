from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_BASE = "https://mess.local/problems"

CODE_TYPE = {
    "AUTH_INVALID_CREDENTIALS": "invalid-credentials",
    "AUTH_INACTIVE": "inactive",
    "AUTH_UNAUTHORIZED": "unauthorized",
    "VALIDATION_ERROR": "validation",
    "CONFLICT_RAB_ID": "conflict-rab-id",
    "INTERNAL_ERROR": "internal",
    "ZK_DEMO_DISABLED": "zk-demo-disabled",
    "ZK_UNREACHABLE": "zk-unreachable",
}

CODE_TITLE = {
    "AUTH_INVALID_CREDENTIALS": "Invalid credentials",
    "AUTH_INACTIVE": "Inactive account",
    "AUTH_UNAUTHORIZED": "Unauthorized",
    "VALIDATION_ERROR": "Validation failed",
    "CONFLICT_RAB_ID": "Conflict",
    "INTERNAL_ERROR": "Internal error",
    "ZK_DEMO_DISABLED": "ZK demo disabled",
    "ZK_UNREACHABLE": "ZK device unreachable",
}


class ApiError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status: int,
        detail: str,
        errors: list[dict[str, str]] | None = None,
        title: str | None = None,
    ) -> None:
        self.code = code
        self.status = status
        self.detail = detail
        self.errors = errors or []
        self.title = title or CODE_TITLE.get(code, "Error")


def problem_body(
    *,
    code: str,
    status: int,
    detail: str,
    instance: str,
    errors: list[dict[str, str]] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    slug = CODE_TYPE.get(code, code.lower().replace("_", "-"))
    return {
        "ok": False,
        "type": f"{PROBLEM_BASE}/{slug}",
        "title": title or CODE_TITLE.get(code, "Error"),
        "status": status,
        "code": code,
        "detail": detail,
        "instance": instance,
        "errors": errors or [],
        "meta": {},
    }


def problem_response(
    *,
    code: str,
    status: int,
    detail: str,
    instance: str,
    errors: list[dict[str, str]] | None = None,
    title: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=problem_body(
            code=code,
            status=status,
            detail=detail,
            instance=instance,
            errors=errors,
            title=title,
        ),
        media_type="application/problem+json",
    )


def _loc_to_field(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return ".".join(parts) if parts else "body"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return problem_response(
            code=exc.code,
            status=exc.status,
            detail=exc.detail,
            instance=request.url.path,
            errors=exc.errors,
            title=exc.title,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            errors.append(
                {
                    "field": _loc_to_field(tuple(err.get("loc", ()))),
                    "code": "REQUIRED" if err.get("type") == "missing" else "INVALID",
                    "message": str(err.get("msg", "Invalid")),
                }
            )
        return problem_response(
            code="VALIDATION_ERROR",
            status=422,
            detail="One or more fields are invalid.",
            instance=request.url.path,
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 401:
            code, detail = "AUTH_UNAUTHORIZED", "Missing or invalid token."
        elif exc.status_code == 403:
            code, detail = "AUTH_INACTIVE", "This staff account is inactive."
        else:
            code, detail = "INTERNAL_ERROR", "Something went wrong."
        return problem_response(
            code=code,
            status=exc.status_code,
            detail=str(exc.detail) if isinstance(exc.detail, str) else detail,
            instance=request.url.path,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(
            code="INTERNAL_ERROR",
            status=500,
            detail="Something went wrong.",
            instance=request.url.path,
        )
