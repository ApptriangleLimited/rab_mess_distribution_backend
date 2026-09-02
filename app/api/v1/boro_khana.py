from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.staff import StaffAccount
from app.schemas.boro_khana import BoroKhanaPutIn
from app.services.assignments import assert_range_size
from app.services.boro_khana import list_boro_khana_dates, set_boro_khana

router = APIRouter(prefix="/api/v1/boro-khana", tags=["boro-khana"])


@router.get("")
def get_boro_khana_dates(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
):
    assert_range_size(from_date, to_date)
    return ok(
        {
            "dates": list_boro_khana_dates(db, from_date, to_date),
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }
    )


@router.put("/{duty_date}")
def put_boro_khana_date(
    duty_date: date,
    body: BoroKhanaPutIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    data = set_boro_khana(db, staff, duty_date, on=body.on)
    db.commit()
    return ok(data)
