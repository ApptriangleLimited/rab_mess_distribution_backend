from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.staff import StaffAccount

_bearer = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_staff(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> StaffAccount:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=401,
            detail="Missing or invalid token.",
        )
    try:
        staff_id = decode_access_token(creds.credentials)
    except InvalidTokenError:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=401,
            detail="Missing or invalid token.",
        ) from None
    staff = db.get(StaffAccount, staff_id)
    if staff is None:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=401,
            detail="Missing or invalid token.",
        )
    if not staff.is_active:
        raise ApiError(
            code="AUTH_INACTIVE",
            status=403,
            detail="This staff account is inactive.",
        )
    return staff


def get_optional_staff(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> StaffAccount | None:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        return None
    try:
        staff_id = decode_access_token(creds.credentials)
    except InvalidTokenError:
        return None
    staff = db.get(StaffAccount, staff_id)
    if staff is None or not staff.is_active:
        return None
    return staff
