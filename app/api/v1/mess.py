from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.member_serialize import member_public
from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.models.member import Member
from app.models.staff import StaffAccount
from app.services.assignments import assert_range_size
from app.services.mess import get_mess_eaters, get_mess_ledger

router = APIRouter(prefix="/api/v1/mess", tags=["mess"])


def _load_members(db: Session, member_ids: list[str]) -> dict[str, Member]:
    if not member_ids:
        return {}
    rows = db.query(Member).filter(Member.id.in_(member_ids)).all()
    return {row.id: row for row in rows}


@router.get("/eaters")
def list_mess_eaters(
    duty_date: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    rank: str | None = Query(None),
    wing: str | None = Query(None),
    q: str | None = Query(None),
):
    rows, boro_khana = get_mess_eaters(
        db,
        duty_date,
        rank=rank,
        wing=wing,
        q=q,
    )
    members = _load_members(db, [row.member_id for row in rows])
    items = []
    for row in rows:
        member = members.get(row.member_id)
        if member is None:
            continue
        items.append(
            {
                **member_public(member),
                "assignment_id": row.assignment_id,
                "mess_reason": row.mess_reason,
            }
        )
    return ok(
        {
            "date": duty_date.isoformat(),
            "boro_khana": boro_khana,
            "items": items,
            "total": len(items),
        }
    )


@router.get("/ledger")
def list_mess_ledger(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    rank: str | None = Query(None),
    wing: str | None = Query(None),
    q: str | None = Query(None),
    preview_future: bool = Query(True),
):
    assert_range_size(from_date, to_date)
    ledger = get_mess_ledger(
        db,
        from_date,
        to_date,
        rank=rank,
        wing=wing,
        q=q,
        preview_future=preview_future,
    )
    members = _load_members(db, [row.member_id for row in ledger.rows])
    return ok(
        {
            "from": ledger.from_date.isoformat(),
            "to": ledger.to_date.isoformat(),
            "dates": ledger.dates,
            "tag_codes": ledger.tag_codes,
            "rows": [
                {
                    "member": member_public(members[row.member_id]),
                    "days": row.days,
                    "tag_counts": row.tag_counts,
                    "total_days": row.total_days,
                }
                for row in ledger.rows
                if row.member_id in members
            ],
            "boro_khana_days": [
                {"date": bk_date, "eater_count": eater_count}
                for bk_date, eater_count in ledger.boro_khana_days
            ],
        }
    )
