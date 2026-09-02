"""Shared member insert used by public register + staff POST /members."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.member import Member, MemberEmergencyContact
from app.schemas.member import MemberEntryIn


def insert_member(
    db: Session,
    body: MemberEntryIn,
    *,
    status: str,
    approval_status: str,
    created_via: str,
) -> Member:
    existing = db.query(Member).filter(Member.rab_id == body.rab_id).one_or_none()
    if existing is not None:
        raise ApiError(
            code="CONFLICT_RAB_ID",
            status=409,
            detail="This RAB ID is already used.",
        )

    rank = "" if body.member_type == "new" else body.rank.strip()
    wing = "" if body.member_type == "new" else body.wing.strip()
    contacts = [
        MemberEmergencyContact(
            name=c.name.strip(),
            relation=c.relation.strip(),
            phone=c.phone.strip(),
        )
        for c in body.emergency_contacts
        if c.name.strip() or c.relation.strip() or c.phone.strip()
    ]
    member = Member(
        name=body.name,
        personal_id=body.personal_id.strip(),
        rab_id=body.rab_id,
        rfid=body.rfid.strip(),
        rank=rank,
        wing=wing,
        member_type=body.member_type,
        dropdown_no=body.dropdown_no.strip(),
        phone=body.phone.strip(),
        status=status,
        approval_status=approval_status,
        created_via=created_via,
        bank_name=body.bank_name.strip(),
        account_name=body.account_name.strip(),
        account_number=body.account_number.strip(),
        routing=body.routing.strip(),
        branch=body.branch.strip(),
        branch_location=body.branch_location.strip(),
        joining_date=body.joining_date,
        out_date=body.out_date,
        default_tag=(body.default_tag or "MS").strip().upper() or "MS",
        documents=[d.model_dump() for d in body.documents],
        emergency_contacts=contacts,
    )
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(
            code="CONFLICT_RAB_ID",
            status=409,
            detail="This RAB ID is already used.",
        ) from None
    db.refresh(member)
    return member
