"""Day lock + approve carry — see docs/DAILY_COCKPIT_API_PLAN.md §5.5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.daily import ApprovedDate, DailyAssignment, SuppressedCarry
from app.models.staff import StaffAccount
from app.services.assignments import require_daily_writer
from app.services.carry import (
    can_assign_on_date,
    is_date_locked,
    list_locked_dates,
    load_stored_map,
    load_suppressed_set,
    query_roster_members,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class ApproveDayResult:
    date: date
    filled: int
    locked: bool


def get_day_lock(db: Session, duty_date: date) -> dict:
    return {
        "date": duty_date.isoformat(),
        "locked": is_date_locked(db, duty_date),
    }


def list_day_locks(db: Session, from_date: date, to_date: date) -> list[str]:
    locked = list_locked_dates(db, from_date, to_date)
    return sorted(d.isoformat() for d in locked)


def approve_day(
    db: Session,
    staff: StaffAccount,
    duty_date: date,
) -> ApproveDayResult:
    require_daily_writer(staff)

    if is_date_locked(db, duty_date):
        return ApproveDayResult(date=duty_date, filled=0, locked=True)

    members = query_roster_members(db)
    eligible = [member for member in members if can_assign_on_date(member, duty_date)]
    if not eligible:
        if not is_date_locked(db, duty_date):
            db.add(
                ApprovedDate(
                    date=duty_date,
                    approved_by=staff.id,
                    approved_at=_utcnow(),
                )
            )
            db.flush()
        return ApproveDayResult(date=duty_date, filled=0, locked=True)

    member_ids = [member.id for member in eligible]
    current_stored = load_stored_map(db, member_ids, duty_date, duty_date)
    suppressed = load_suppressed_set(db, member_ids, duty_date, duty_date)
    now = _utcnow()
    filled = 0

    for member in eligible:
        key = (member.id, duty_date)
        stored_row = current_stored.get(key)
        suppressed_here = key in suppressed

        if stored_row is not None and not suppressed_here:
            continue

        fill_tag = (member.default_tag or "").strip().upper() or None
        if fill_tag is None:
            db.query(SuppressedCarry).filter(
                SuppressedCarry.member_id == member.id,
                SuppressedCarry.date == duty_date,
            ).delete()
            continue

        if stored_row is None:
            stored_row = DailyAssignment(
                member_id=member.id,
                date=duty_date,
                tag=fill_tag,
                updated_by=staff.id,
                updated_at=now,
            )
            db.add(stored_row)
        else:
            stored_row.tag = fill_tag
            stored_row.updated_by = staff.id
            stored_row.updated_at = now

        db.query(SuppressedCarry).filter(
            SuppressedCarry.member_id == member.id,
            SuppressedCarry.date == duty_date,
        ).delete()
        filled += 1

    if not is_date_locked(db, duty_date):
        db.add(
            ApprovedDate(
                date=duty_date,
                approved_by=staff.id,
                approved_at=now,
            )
        )
    db.flush()
    return ApproveDayResult(date=duty_date, filled=filled, locked=True)
