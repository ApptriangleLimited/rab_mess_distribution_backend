"""Member approval transitions — see docs/MEMBER_APPROVAL_PLAN.md."""

from sqlalchemy.orm import Session, joinedload

from app.api.v1.member_serialize import normalize_approval
from app.core.errors import ApiError
from app.models.member import Member
from app.models.member_constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING_CC,
    APPROVAL_PENDING_DAILY,
    APPROVAL_REJECTED,
)
from app.models.staff import StaffAccount

_CC_REVIEW_ROLES = frozenset({"cc", "admin"})
_DAILY_REVIEW_ROLES = frozenset({"daily", "admin"})


def _get_member(db: Session, member_id: str) -> Member:
    member = (
        db.query(Member)
        .options(joinedload(Member.emergency_contacts))
        .filter(Member.id == member_id)
        .one_or_none()
    )
    if member is None:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=404,
            detail="Member not found.",
        )
    return member


def _require_role(staff: StaffAccount, allowed: frozenset[str], action: str) -> None:
    if staff.role not in allowed:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=403,
            detail=f"This role cannot {action}.",
        )


def _require_status(member: Member, expected: str) -> None:
    current = normalize_approval(member.approval_status)
    if current != expected:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail=f"Member must be {expected} for this action.",
            errors=[
                {
                    "field": "approval_status",
                    "code": "INVALID",
                    "message": f"Current status is {current}.",
                }
            ],
        )


def _save(db: Session, member: Member) -> Member:
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def cc_accept_member(db: Session, staff: StaffAccount, member_id: str) -> Member:
    _require_role(staff, _CC_REVIEW_ROLES, "review at CC")
    member = _get_member(db, member_id)
    _require_status(member, APPROVAL_PENDING_CC)
    member.approval_status = APPROVAL_PENDING_DAILY
    return _save(db, member)


def cc_reject_member(db: Session, staff: StaffAccount, member_id: str) -> Member:
    _require_role(staff, _CC_REVIEW_ROLES, "reject at CC")
    member = _get_member(db, member_id)
    _require_status(member, APPROVAL_PENDING_CC)
    member.approval_status = APPROVAL_REJECTED
    return _save(db, member)


def approve_member(db: Session, staff: StaffAccount, member_id: str) -> Member:
    _require_role(staff, _DAILY_REVIEW_ROLES, "approve for duty")
    member = _get_member(db, member_id)
    _require_status(member, APPROVAL_PENDING_DAILY)
    member.approval_status = APPROVAL_APPROVED
    member.status = "1"
    return _save(db, member)


def reject_member(db: Session, staff: StaffAccount, member_id: str) -> Member:
    _require_role(staff, _DAILY_REVIEW_ROLES, "reject at Daily")
    member = _get_member(db, member_id)
    _require_status(member, APPROVAL_PENDING_DAILY)
    member.approval_status = APPROVAL_REJECTED
    return _save(db, member)
