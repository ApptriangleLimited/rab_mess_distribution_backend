"""Staff POST /members — role sets approval path."""

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.member import Member
from app.models.member_constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING_DAILY,
    CREATED_VIA_CC,
    CREATED_VIA_DAILY,
)
from app.models.staff import StaffAccount
from app.schemas.member import MemberCreateIn
from app.services.member_create import insert_member

_STAFF_CREATE_ROLES = frozenset({"cc", "daily", "admin"})


def create_staff_member(
    db: Session,
    staff: StaffAccount,
    body: MemberCreateIn,
) -> Member:
    if staff.role not in _STAFF_CREATE_ROLES:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=403,
            detail="This role cannot create members.",
        )

    if staff.role == "daily":
        return insert_member(
            db,
            body,
            status="1",
            approval_status=APPROVAL_APPROVED,
            created_via=CREATED_VIA_DAILY,
        )

    # cc + admin → Daily queue (client status/approval ignored).
    return insert_member(
        db,
        body,
        status="0",
        approval_status=APPROVAL_PENDING_DAILY,
        created_via=CREATED_VIA_CC,
    )
