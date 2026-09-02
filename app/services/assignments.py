"""Assignment writes for Daily Cockpit — see docs/DAILY_COCKPIT_API_PLAN.md §5.4."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.lib.dates import each_date
from app.models.daily import ApprovedDate, DailyAssignment, SuppressedCarry
from app.models.member import Member
from app.models.staff import StaffAccount
from app.services.carry import (
    ProjectedCell,
    can_assign_on_date,
    is_known_paint_tag,
    is_roster_member,
    project_cell,
)

_MAX_RANGE_DAYS = 31
_DAILY_WRITE_ROLES = frozenset({"daily", "admin"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def require_daily_writer(staff: StaffAccount) -> None:
    if staff.role not in _DAILY_WRITE_ROLES:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=403,
            detail="This role cannot edit assignments.",
        )


def assert_range_size(from_date: date, to_date: date) -> None:
    days = len(each_date(from_date, to_date))
    if days > _MAX_RANGE_DAYS:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Date range cannot exceed 31 days.",
            errors=[
                {
                    "field": "to",
                    "code": "INVALID",
                    "message": "Date range cannot exceed 31 days.",
                }
            ],
        )


def assert_paintable_date(duty_date: date) -> None:
    if duty_date <= date.today():
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Past and today are not editable.",
            errors=[
                {
                    "field": "date",
                    "code": "INVALID",
                    "message": "Past and today are not editable.",
                }
            ],
        )


def _get_roster_member(db: Session, member_id: str) -> Member:
    member = db.get(Member, member_id)
    if member is None or not is_roster_member(member):
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Member is not on the active roster.",
            errors=[
                {
                    "field": "member_id",
                    "code": "INVALID",
                    "message": "Member is not on the active roster.",
                }
            ],
        )
    return member


def _assert_writable_cell(
    db: Session,
    member: Member,
    duty_date: date,
    *,
    field: str = "date",
) -> None:
    assert_paintable_date(duty_date)
    if not can_assign_on_date(member, duty_date):
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Date is after member out date.",
            errors=[
                {
                    "field": field,
                    "code": "INVALID",
                    "message": "Date is after member out date.",
                }
            ],
        )


def _assert_known_tag(db: Session, tag: str) -> str:
    normalized = tag.strip().upper()
    if not is_known_paint_tag(db, normalized):
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Unknown tag.",
            errors=[
                {
                    "field": "tag",
                    "code": "INVALID",
                    "message": "Unknown tag.",
                }
            ],
        )
    return normalized


def _unapprove_date(db: Session, duty_date: date) -> None:
    db.query(ApprovedDate).filter(ApprovedDate.date == duty_date).delete()


def _remove_suppression(db: Session, member_id: str, duty_date: date) -> None:
    db.query(SuppressedCarry).filter(
        SuppressedCarry.member_id == member_id,
        SuppressedCarry.date == duty_date,
    ).delete()


def _add_suppression(db: Session, member_id: str, duty_date: date) -> None:
    exists = (
        db.query(SuppressedCarry)
        .filter(
            SuppressedCarry.member_id == member_id,
            SuppressedCarry.date == duty_date,
        )
        .first()
    )
    if exists is None:
        db.add(SuppressedCarry(member_id=member_id, date=duty_date))


def _stored_cell(
    db: Session,
    member: Member,
    duty_date: date,
    *,
    stored: DailyAssignment | None = None,
) -> ProjectedCell:
    stored_map = {(member.id, duty_date): stored} if stored else {}
    suppressed = (
        db.query(SuppressedCarry.member_id, SuppressedCarry.date)
        .filter(
            SuppressedCarry.member_id == member.id,
            SuppressedCarry.date == duty_date,
        )
        .all()
    )
    return project_cell(
        member=member,
        duty_date=duty_date,
        stored_map=stored_map,
        suppressed={(row[0], row[1]) for row in suppressed},
    )


def set_assignment(
    db: Session,
    staff: StaffAccount,
    *,
    member_id: str,
    duty_date: date,
    tag: str,
) -> ProjectedCell:
    require_daily_writer(staff)
    member = _get_roster_member(db, member_id)
    _assert_writable_cell(db, member, duty_date)
    normalized_tag = _assert_known_tag(db, tag)

    row = (
        db.query(DailyAssignment)
        .filter(
            DailyAssignment.member_id == member_id,
            DailyAssignment.date == duty_date,
        )
        .one_or_none()
    )
    now = _utcnow()
    if row is None:
        row = DailyAssignment(
            member_id=member_id,
            date=duty_date,
            tag=normalized_tag,
            updated_by=staff.id,
            updated_at=now,
        )
        db.add(row)
    else:
        row.tag = normalized_tag
        row.updated_by = staff.id
        row.updated_at = now

    _remove_suppression(db, member_id, duty_date)
    _unapprove_date(db, duty_date)
    db.flush()
    return _stored_cell(db, member, duty_date, stored=row)


def clear_assignment(
    db: Session,
    staff: StaffAccount,
    *,
    member_id: str,
    duty_date: date,
) -> ProjectedCell:
    require_daily_writer(staff)
    member = _get_roster_member(db, member_id)
    _assert_writable_cell(db, member, duty_date)

    db.query(DailyAssignment).filter(
        DailyAssignment.member_id == member_id,
        DailyAssignment.date == duty_date,
    ).delete()
    _add_suppression(db, member_id, duty_date)
    _unapprove_date(db, duty_date)
    db.flush()
    return _stored_cell(db, member, duty_date)


def set_assignment_bulk(
    db: Session,
    staff: StaffAccount,
    *,
    duty_date: date,
    tag: str,
    member_ids: list[str],
) -> tuple[int, list[ProjectedCell]]:
    items: list[ProjectedCell] = []
    updated = 0
    for member_id in member_ids:
        cell = set_assignment(
            db,
            staff,
            member_id=member_id,
            duty_date=duty_date,
            tag=tag,
        )
        items.append(cell)
        updated += 1
    return updated, items


def set_assignment_range(
    db: Session,
    staff: StaffAccount,
    *,
    member_id: str,
    dates: list[date],
    tag: str,
) -> tuple[int, list[ProjectedCell]]:
    items: list[ProjectedCell] = []
    updated = 0
    normalized_tag = tag.strip().upper() if tag else ""

    for duty_date in dates:
        if normalized_tag:
            cell = set_assignment(
                db,
                staff,
                member_id=member_id,
                duty_date=duty_date,
                tag=normalized_tag,
            )
        else:
            cell = clear_assignment(
                db,
                staff,
                member_id=member_id,
                duty_date=duty_date,
            )
        items.append(cell)
        updated += 1
    return updated, items
