from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.core.errors import ApiError
from app.core.security import (
    access_expires_in,
    create_access_token,
    verify_password,
)
from app.models.staff import StaffAccount
from app.schemas.auth import LoginIn

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _staff_public(staff: StaffAccount) -> dict[str, str]:
    return {
        "id": staff.id,
        "email": staff.email,
        "display_name": staff.display_name,
        "role": staff.role,
    }


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    staff = (
        db.query(StaffAccount)
        .filter(StaffAccount.email == str(body.email).lower())
        .one_or_none()
    )
    if staff is None or not verify_password(body.password, staff.password_hash):
        raise ApiError(
            code="AUTH_INVALID_CREDENTIALS",
            status=401,
            detail="Email or password is wrong.",
        )
    if not staff.is_active:
        raise ApiError(
            code="AUTH_INACTIVE",
            status=403,
            detail="This staff account is inactive.",
        )
    token = create_access_token(staff.id)
    return ok(
        {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": access_expires_in(),
            "staff": _staff_public(staff),
        }
    )


@router.get("/me")
def me(staff: StaffAccount = Depends(get_current_staff)):
    return ok(_staff_public(staff))


@router.post("/logout")
def logout(_staff: StaffAccount = Depends(get_current_staff)):
    return Response(status_code=204)
