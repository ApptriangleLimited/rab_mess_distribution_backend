from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.v1.member_serialize import approval_db_values, member_public, normalize_approval
from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.member import Member
from app.models.staff import StaffAccount
from app.schemas.member import MemberCreateIn
from app.services.member_staff_create import create_staff_member
from app.services.member_transitions import (
    approve_member,
    cc_accept_member,
    cc_reject_member,
    reject_member,
)

router = APIRouter(prefix="/api/v1/members", tags=["members"])


@router.post("")
def create_member(
    body: MemberCreateIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    member = create_staff_member(db, staff, body)
    return ok(
        member_public(member),
        status=201,
        headers={"Location": f"/api/v1/members/{member.id}"},
    )


@router.get("")
def list_members(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    q: str | None = Query(None),
    status: str | None = Query(None),
    approval: str | None = Query(None),
    wing: str | None = Query(None),
    rank: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
):
    query = db.query(Member).options(joinedload(Member.emergency_contacts))

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Member.name.ilike(term),
                Member.rab_id.ilike(term),
                Member.phone.ilike(term),
                Member.personal_id.ilike(term),
            )
        )
    if status in ("0", "1"):
        query = query.filter(Member.status == status)
    if approval and approval not in ("all", ""):
        wanted = normalize_approval(approval)
        values = approval_db_values(wanted)
        query = query.filter(Member.approval_status.in_(values))
    if wing and wing not in ("all", ""):
        query = query.filter(Member.wing == wing)
    if rank and rank not in ("all", ""):
        query = query.filter(Member.rank == rank)
    if date_from:
        query = query.filter(
            or_(Member.joining_date >= date_from, Member.out_date >= date_from)
        )
    if date_to:
        query = query.filter(
            or_(Member.joining_date <= date_to, Member.out_date <= date_to)
        )

    total = query.count()
    rows = (
        query.order_by(Member.rab_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(
        {
            "items": [member_public(m) for m in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/{member_id}/cc-accept")
def cc_accept(
    member_id: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    member = cc_accept_member(db, staff, member_id)
    return ok(member_public(member))


@router.post("/{member_id}/cc-reject")
def cc_reject(
    member_id: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    member = cc_reject_member(db, staff, member_id)
    return ok(member_public(member))


@router.post("/{member_id}/approve")
def approve(
    member_id: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    member = approve_member(db, staff, member_id)
    return ok(member_public(member))


@router.post("/{member_id}/reject")
def reject(
    member_id: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    member = reject_member(db, staff, member_id)
    return ok(member_public(member))
