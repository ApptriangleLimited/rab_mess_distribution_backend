from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.assignment_serialize import (
    assignment_cell_public,
    assignment_summary_public,
)
from app.core.deps import get_current_staff, get_db
from app.core.envelope import ok
from app.lib.dates import month_bounds
from app.models.staff import StaffAccount
from app.schemas.assignment import (
    AssignmentBulkPutIn,
    AssignmentPutIn,
    AssignmentRangePutIn,
)
from app.services.assignments import (
    assert_range_size,
    clear_assignment,
    set_assignment,
    set_assignment_bulk,
    set_assignment_range,
)
from app.services.carry import project_assignments, summarize_assignments

router = APIRouter(prefix="/api/v1/assignments", tags=["assignments"])


def _resolve_range(
    *,
    month: str | None,
    from_date: date | None,
    to_date: date | None,
    single_date: date | None,
) -> tuple[date, date]:
    if month:
        start, end = month_bounds(month)
        assert_range_size(start, end)
        return start, end
    if single_date is not None:
        return single_date, single_date
    if from_date is None or to_date is None:
        raise ValueError("range")
    assert_range_size(from_date, to_date)
    return from_date, to_date


@router.get("")
def list_assignments(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    month: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    single_date: date | None = Query(None, alias="date"),
    member_id: str | None = Query(None),
    rank: str | None = Query(None),
    wing: str | None = Query(None),
    q: str | None = Query(None),
):
    try:
        start, end = _resolve_range(
            month=month,
            from_date=from_date,
            to_date=to_date,
            single_date=single_date,
        )
    except ValueError:
        from app.core.errors import ApiError

        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Provide month, date, or from/to.",
            errors=[
                {
                    "field": "from",
                    "code": "REQUIRED",
                    "message": "Provide month, date, or from/to.",
                }
            ],
        ) from None

    cells = project_assignments(
        db,
        from_date=start,
        to_date=end,
        member_id=member_id,
        rank=rank,
        wing=wing,
        q=q,
    )
    return ok(
        {
            "items": [assignment_cell_public(cell) for cell in cells],
            "from": start.isoformat(),
            "to": end.isoformat(),
        }
    )


@router.get("/summary")
def assignment_summary(
    db: Session = Depends(get_db),
    _staff: StaffAccount = Depends(get_current_staff),
    month: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    member_id: str | None = Query(None),
    rank: str | None = Query(None),
    wing: str | None = Query(None),
    q: str | None = Query(None),
):
    try:
        start, end = _resolve_range(
            month=month,
            from_date=from_date,
            to_date=to_date,
            single_date=None,
        )
    except ValueError:
        from app.core.errors import ApiError

        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Provide month or from/to.",
            errors=[
                {
                    "field": "from",
                    "code": "REQUIRED",
                    "message": "Provide month or from/to.",
                }
            ],
        ) from None

    summary = summarize_assignments(
        db,
        from_date=start,
        to_date=end,
        member_id=member_id,
        rank=rank,
        wing=wing,
        q=q,
    )
    return ok(assignment_summary_public(summary))


@router.put("/bulk")
def put_assignments_bulk(
    body: AssignmentBulkPutIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    updated, items = set_assignment_bulk(
        db,
        staff,
        duty_date=body.date,
        tag=body.tag,
        member_ids=body.member_ids,
    )
    db.commit()
    return ok(
        {
            "updated": updated,
            "items": [assignment_cell_public(cell) for cell in items],
        }
    )


@router.put("/range")
def put_assignments_range(
    body: AssignmentRangePutIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    if len(body.dates) > 31:
        from app.core.errors import ApiError

        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Date range cannot exceed 31 days.",
            errors=[
                {
                    "field": "dates",
                    "code": "INVALID",
                    "message": "Date range cannot exceed 31 days.",
                }
            ],
        )
    updated, items = set_assignment_range(
        db,
        staff,
        member_id=body.member_id,
        dates=body.dates,
        tag=body.tag,
    )
    db.commit()
    return ok(
        {
            "updated": updated,
            "items": [assignment_cell_public(cell) for cell in items],
        }
    )


@router.put("")
def put_assignment(
    body: AssignmentPutIn,
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
):
    cell = set_assignment(
        db,
        staff,
        member_id=body.member_id,
        duty_date=body.date,
        tag=body.tag,
    )
    db.commit()
    return ok({"items": [assignment_cell_public(cell)]})


@router.delete("")
def delete_assignment(
    db: Session = Depends(get_db),
    staff: StaffAccount = Depends(get_current_staff),
    member_id: str = Query(...),
    duty_date: date = Query(..., alias="date"),
):
    cell = clear_assignment(
        db,
        staff,
        member_id=member_id,
        duty_date=duty_date,
    )
    db.commit()
    return ok({"items": [assignment_cell_public(cell)]})
