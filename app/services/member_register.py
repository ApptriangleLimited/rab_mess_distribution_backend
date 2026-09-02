"""Public member entry — `/api/v1/public/register`."""

from sqlalchemy.orm import Session

from app.models.member import Member
from app.models.member_constants import (
    APPROVAL_PENDING_CC,
    CREATED_VIA_PUBLIC,
)
from app.schemas.member import MemberEntryIn
from app.services.member_create import insert_member


def register_public_member(db: Session, body: MemberEntryIn) -> Member:
    """Self-register: inactive, CC queue first. Client cannot override status."""
    return insert_member(
        db,
        body,
        status="0",
        approval_status=APPROVAL_PENDING_CC,
        created_via=CREATED_VIA_PUBLIC,
    )
