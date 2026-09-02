from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.staff import StaffAccount
from app.schemas.settings import SenderIn
from app.services.senders import (
    create_sender,
    delete_sender,
    get_sender,
    list_senders,
    sender_public,
    update_sender,
)

router = APIRouter(prefix="/api/v1/senders", tags=["senders"])


@router.get("")
def get_senders(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
):
    rows = list_senders(db)
    return ok({"items": [sender_public(row) for row in rows]})


@router.post("")
def post_sender(
    body: SenderIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    row = create_sender(
        db,
        staff,
        label=body.label,
        bank_name=body.bank_name,
        account_name=body.account_name,
        account_number=body.account_number,
        routing=body.routing,
        branch=body.branch,
        branch_location=body.branch_location,
        mapped_tags=body.mapped_tags,
        active=body.active,
    )
    db.commit()
    return ok(sender_public(row), status=201)


@router.put("/{sender_id}")
def put_sender(
    sender_id: str,
    body: SenderIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    row = update_sender(
        db,
        staff,
        sender_id,
        label=body.label,
        bank_name=body.bank_name,
        account_name=body.account_name,
        account_number=body.account_number,
        routing=body.routing,
        branch=body.branch,
        branch_location=body.branch_location,
        mapped_tags=body.mapped_tags,
        active=body.active,
    )
    db.commit()
    return ok(sender_public(row))


@router.delete("/{sender_id}")
def remove_sender(
    sender_id: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    delete_sender(db, staff, sender_id)
    db.commit()
    return ok({"id": sender_id})
