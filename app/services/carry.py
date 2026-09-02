"""Carry projection + assignment summaries for Daily Cockpit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.constants.allowance import (
    BUILTIN_DAILY_TAGS,
    DEFAULT_BUILTIN_RATES,
    RATE_ONLY_TAGS,
)
from app.lib.dates import each_date, extend_back, previous_date
from app.models.allowance_rate import AllowanceRate
from app.models.daily import ApprovedDate, DailyAssignment, SuppressedCarry
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED

MAX_CARRY_LOOKBACK_DAYS = 62

AssignmentSource = Literal["stored", "carry", "empty", "suppressed"]


@dataclass(frozen=True)
class ProjectedCell:
    member_id: str
    date: date
    tag: str | None
    source: AssignmentSource
    updated_at: datetime | None = None
    updated_by: str | None = None


@dataclass(frozen=True)
class AssignmentSummary:
    from_date: date
    to_date: date
    by_tag: dict[str, int]
    total_tagged_person_days: int
    member_count: int


def can_assign_on_date(member: Member, duty_date: date) -> bool:
    if member.out_date is not None and duty_date > member.out_date:
        return False
    return True


def is_roster_member(member: Member) -> bool:
    return member.approval_status == APPROVAL_APPROVED and member.status == "1"


def list_paint_tags(db: Session) -> list[str]:
    rows = db.query(AllowanceRate.tag).order_by(AllowanceRate.tag.asc()).all()
    tags = [row[0] for row in rows if row[0] not in RATE_ONLY_TAGS]
    if tags:
        return tags
    return list(BUILTIN_DAILY_TAGS)


def is_known_paint_tag(db: Session, tag: str) -> bool:
    normalized = tag.strip().upper()
    if not normalized:
        return False
    if normalized in RATE_ONLY_TAGS:
        return False
    return normalized in {t.upper() for t in list_paint_tags(db)}


def is_date_locked(db: Session, duty_date: date) -> bool:
    return (
        db.query(ApprovedDate.date)
        .filter(ApprovedDate.date == duty_date)
        .first()
        is not None
    )


def list_locked_dates(db: Session, from_date: date, to_date: date) -> set[date]:
    rows = (
        db.query(ApprovedDate.date)
        .filter(ApprovedDate.date >= from_date, ApprovedDate.date <= to_date)
        .all()
    )
    return {row[0] for row in rows}


def load_stored_map(
    db: Session,
    member_ids: list[str],
    from_date: date,
    to_date: date,
) -> dict[tuple[str, date], DailyAssignment]:
    if not member_ids:
        return {}
    rows = (
        db.query(DailyAssignment)
        .filter(
            DailyAssignment.member_id.in_(member_ids),
            DailyAssignment.date >= from_date,
            DailyAssignment.date <= to_date,
        )
        .all()
    )
    return {(row.member_id, row.date): row for row in rows}


def load_suppressed_set(
    db: Session,
    member_ids: list[str],
    from_date: date,
    to_date: date,
) -> set[tuple[str, date]]:
    if not member_ids:
        return set()
    rows = (
        db.query(SuppressedCarry.member_id, SuppressedCarry.date)
        .filter(
            SuppressedCarry.member_id.in_(member_ids),
            SuppressedCarry.date >= from_date,
            SuppressedCarry.date <= to_date,
        )
        .all()
    )
    return {(member_id, duty_date) for member_id, duty_date in rows}


def find_prior_stored_tag(
    stored_map: dict[tuple[str, date], DailyAssignment],
    member_id: str,
    duty_date: date,
    *,
    max_days: int = MAX_CARRY_LOOKBACK_DAYS,
) -> str | None:
    cursor = previous_date(duty_date)
    for _ in range(max_days):
        stored = stored_map.get((member_id, cursor))
        if stored is not None:
            return stored.tag
        cursor = previous_date(cursor)
    return None


def project_cell(
    *,
    member: Member,
    duty_date: date,
    stored_map: dict[tuple[str, date], DailyAssignment],
    suppressed: set[tuple[str, date]],
) -> ProjectedCell:
    stored = stored_map.get((member.id, duty_date))
    if stored is not None:
        return ProjectedCell(
            member_id=member.id,
            date=duty_date,
            tag=stored.tag,
            source="stored",
            updated_at=stored.updated_at,
            updated_by=stored.updated_by,
        )

    if (member.id, duty_date) in suppressed:
        return ProjectedCell(
            member_id=member.id,
            date=duty_date,
            tag=None,
            source="suppressed",
        )

    # Inactive / left roster: no default ghost — empty cells stay blank.
    if not is_roster_member(member) or not can_assign_on_date(member, duty_date):
        return ProjectedCell(
            member_id=member.id,
            date=duty_date,
            tag=None,
            source="empty",
        )

    default = (member.default_tag or "").strip().upper() or None
    if default is not None:
        return ProjectedCell(
            member_id=member.id,
            date=duty_date,
            tag=default,
            source="carry",
        )

    return ProjectedCell(
        member_id=member.id,
        date=duty_date,
        tag=None,
        source="empty",
    )


def query_roster_members(
    db: Session,
    *,
    member_id: str | None = None,
    rank: str | None = None,
    wing: str | None = None,
    q: str | None = None,
) -> list[Member]:
    # Approved active + inactive — inactive keep prior assignment history.
    query = db.query(Member).filter(
        Member.approval_status == APPROVAL_APPROVED,
    )
    if member_id:
        query = query.filter(Member.id == member_id)
    if rank and rank not in ("all", ""):
        query = query.filter(Member.rank == rank)
    if wing and wing not in ("all", ""):
        query = query.filter(Member.wing == wing)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            Member.name.ilike(term)
            | Member.rab_id.ilike(term)
            | Member.phone.ilike(term)
            | Member.personal_id.ilike(term)
        )
    return query.order_by(Member.rab_id.asc()).all()


def project_assignments(
    db: Session,
    *,
    from_date: date,
    to_date: date,
    member_id: str | None = None,
    rank: str | None = None,
    wing: str | None = None,
    q: str | None = None,
) -> list[ProjectedCell]:
    members = query_roster_members(
        db,
        member_id=member_id,
        rank=rank,
        wing=wing,
        q=q,
    )
    if not members:
        return []

    member_ids = [member.id for member in members]
    lookup_from = extend_back(from_date, MAX_CARRY_LOOKBACK_DAYS)
    stored_map = load_stored_map(db, member_ids, lookup_from, to_date)
    suppressed = load_suppressed_set(db, member_ids, from_date, to_date)

    cells: list[ProjectedCell] = []
    for duty_date in each_date(from_date, to_date):
        for member in members:
            cells.append(
                project_cell(
                    member=member,
                    duty_date=duty_date,
                    stored_map=stored_map,
                    suppressed=suppressed,
                )
            )
    return cells


def summarize_projected(
    cells: list[ProjectedCell],
    *,
    from_date: date,
    to_date: date,
    member_count: int,
) -> AssignmentSummary:
    by_tag: dict[str, int] = {}
    total = 0
    for cell in cells:
        if cell.tag is None:
            continue
        if cell.source not in ("stored", "carry"):
            continue
        by_tag[cell.tag] = by_tag.get(cell.tag, 0) + 1
        total += 1
    return AssignmentSummary(
        from_date=from_date,
        to_date=to_date,
        by_tag=by_tag,
        total_tagged_person_days=total,
        member_count=member_count,
    )


def summarize_assignments(
    db: Session,
    *,
    from_date: date,
    to_date: date,
    member_id: str | None = None,
    rank: str | None = None,
    wing: str | None = None,
    q: str | None = None,
) -> AssignmentSummary:
    members = query_roster_members(
        db,
        member_id=member_id,
        rank=rank,
        wing=wing,
        q=q,
    )
    cells = project_assignments(
        db,
        from_date=from_date,
        to_date=to_date,
        member_id=member_id,
        rank=rank,
        wing=wing,
        q=q,
    )
    return summarize_projected(
        cells,
        from_date=from_date,
        to_date=to_date,
        member_count=len(members),
    )


def seed_builtin_rates(db: Session) -> int:
    created = 0
    for tag, amount in DEFAULT_BUILTIN_RATES.items():
        existing = db.get(AllowanceRate, tag)
        if existing is not None:
            continue
        db.add(
            AllowanceRate(
                tag=tag,
                amount_per_day=amount,
                is_builtin=True,
            )
        )
        created += 1
    return created
