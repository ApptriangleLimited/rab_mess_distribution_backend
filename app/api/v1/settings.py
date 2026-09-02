from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.staff import StaffAccount
from app.schemas.settings import RateCreateIn, RatesReplaceIn, SenderIn
from app.services.settings_rates import (
    add_custom_rate,
    delete_custom_rate,
    list_rates,
    rate_public,
    replace_rate_amounts,
)
from app.services.senders import (
    create_sender,
    delete_sender,
    list_senders,
    sender_public,
    update_sender,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/rates")
def get_rates(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
):
    rows = list_rates(db)
    return ok({"items": [rate_public(row) for row in rows]})


@router.put("/rates")
def put_rates(
    body: RatesReplaceIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    rows = replace_rate_amounts(
        db,
        staff,
        [{"tag": item.tag, "amount_per_day": item.amount_per_day} for item in body.items],
    )
    db.commit()
    return ok({"items": [rate_public(row) for row in rows]})


@router.post("/rates")
def post_rate(
    body: RateCreateIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    row = add_custom_rate(
        db,
        staff,
        tag=body.tag,
        amount_per_day=Decimal(str(body.amount_per_day)),
    )
    db.commit()
    return ok(rate_public(row), status=201)


@router.delete("/rates/{tag}")
def delete_rate(
    tag: str,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    delete_custom_rate(db, staff, tag)
    db.commit()
    return ok({"tag": tag.strip().upper()})
