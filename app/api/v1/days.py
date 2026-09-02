from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.staff import StaffAccount
from app.services.assignments import assert_range_size
from app.services.day_lock import approve_day, get_day_lock, list_day_locks

router = APIRouter(prefix="/api/v1/days", tags=["days"])


@router.get("/locks")
def get_day_locks(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
):
    assert_range_size(from_date, to_date)
    return ok(
        {
            "dates": list_day_locks(db, from_date, to_date),
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }
    )


@router.get("/{duty_date}/lock")
def get_day_lock_status(
    duty_date: date,
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
):
    return ok(get_day_lock(db, duty_date))


@router.post("/{duty_date}/approve")
def post_day_approve(
    duty_date: date,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    result = approve_day(db, staff, duty_date)
    db.commit()
    return ok(
        {
            "date": result.date.isoformat(),
            "filled": result.filled,
            "locked": result.locked,
        }
    )
