"""Mess eaters + ledger — port of frontend `lib/store/mess.ts` + range ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from sqlalchemy.orm import Session

from app.lib.dates import each_date, extend_back
from app.models.daily import DailyAssignment
from app.services.boro_khana import is_boro_khana, list_boro_khana_dates
from app.services.carry import (
    MAX_CARRY_LOOKBACK_DAYS,
    can_assign_on_date,
    load_stored_map,
    load_suppressed_set,
    project_assignments,
    project_cell,
    query_roster_members,
)

MESS_LEDGER_TAGS: tuple[str, ...] = ("MS", "CD")
MessEaterReason = Literal["MS", "FR", "BK"]


@dataclass(frozen=True)
class MessEaterRow:
    member_id: str
    assignment_id: str
    mess_reason: MessEaterReason


@dataclass(frozen=True)
class MessLedgerRow:
    member_id: str
    days: list[str]
    tag_counts: dict[str, int]
    total_days: int


@dataclass(frozen=True)
class MessLedger:
    from_date: date
    to_date: date
    dates: list[str]
    tag_codes: list[str]
    rows: list[MessLedgerRow]
    boro_khana_days: list[tuple[str, int]]


def _reason_for_bk_guest(tag: str | None) -> MessEaterReason:
    if tag == "MS":
        return "MS"
    if tag == "FR":
        return "FR"
    return "BK"


def get_mess_eaters(
    db: Session,
    duty_date: date,
    *,
    rank: str | None = None,
    wing: str | None = None,
    q: str | None = None,
) -> tuple[list[MessEaterRow], bool]:
    members = [
        member
        for member in query_roster_members(db, rank=rank, wing=wing, q=q)
        if can_assign_on_date(member, duty_date)
    ]
    members.sort(key=lambda member: member.rab_id)

    if is_boro_khana(db, duty_date):
        member_ids = [member.id for member in members]
        lookup_from = extend_back(duty_date, MAX_CARRY_LOOKBACK_DAYS)
        stored_map = load_stored_map(db, member_ids, lookup_from, duty_date)
        suppressed = load_suppressed_set(db, member_ids, duty_date, duty_date)
        rows: list[MessEaterRow] = []
        for member in members:
            cell = project_cell(
                member=member,
                duty_date=duty_date,
                stored_map=stored_map,
                suppressed=suppressed,
            )
            stored = stored_map.get((member.id, duty_date))
            assignment_id = (
                stored.id
                if stored is not None
                else f"bk-{member.id}-{duty_date.isoformat()}"
            )
            rows.append(
                MessEaterRow(
                    member_id=member.id,
                    assignment_id=assignment_id,
                    mess_reason=_reason_for_bk_guest(cell.tag),
                )
            )
        return rows, True

    if not members:
        return [], False

    member_ids = [member.id for member in members]
    member_by_id = {member.id: member for member in members}
    assignments = (
        db.query(DailyAssignment)
        .filter(
            DailyAssignment.date == duty_date,
            DailyAssignment.tag == "MS",
            DailyAssignment.member_id.in_(member_ids),
        )
        .order_by(DailyAssignment.member_id.asc())
        .all()
    )
    rows = []
    for assignment in assignments:
        member = member_by_id.get(assignment.member_id)
        if member is None:
            continue
        rows.append(
            MessEaterRow(
                member_id=member.id,
                assignment_id=assignment.id,
                mess_reason="MS",
            )
        )
    rows.sort(key=lambda row: member_by_id[row.member_id].rab_id)
    return rows, False


def get_mess_ledger(
    db: Session,
    from_date: date,
    to_date: date,
    *,
    rank: str | None = None,
    wing: str | None = None,
    q: str | None = None,
    preview_future: bool = True,
) -> MessLedger:
    members = query_roster_members(db, rank=rank, wing=wing, q=q)
    member_by_id = {member.id: member for member in members}
    dates = each_date(from_date, to_date)
    today = date.today()

    cells = project_assignments(
        db,
        from_date=from_date,
        to_date=to_date,
        rank=rank,
        wing=wing,
        q=q,
    )
    cell_map = {(cell.member_id, cell.date): cell for cell in cells}

    rows: list[MessLedgerRow] = []
    for member in members:
        days: list[str] = []
        tag_counts: dict[str, int] = {}
        for duty_date in dates:
            if not can_assign_on_date(member, duty_date):
                days.append("")
                continue
            if duty_date > today and not preview_future:
                days.append("")
                continue
            cell = cell_map.get((member.id, duty_date))
            tag = ""
            if (
                cell is not None
                and cell.tag in MESS_LEDGER_TAGS
                and cell.source in ("stored", "carry")
            ):
                tag = cell.tag
            days.append(tag)
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        total_days = sum(tag_counts.values())
        if total_days == 0:
            continue
        rows.append(
            MessLedgerRow(
                member_id=member.id,
                days=days,
                tag_counts=tag_counts,
                total_days=total_days,
            )
        )

    rows.sort(key=lambda row: member_by_id[row.member_id].rab_id)

    bk_dates = list_boro_khana_dates(db, from_date, to_date)
    boro_khana_days: list[tuple[str, int]] = []
    for bk_date in bk_dates:
        eaters, _ = get_mess_eaters(
            db,
            date.fromisoformat(bk_date),
            rank=rank,
            wing=wing,
            q=q,
        )
        boro_khana_days.append((bk_date, len(eaters)))

    return MessLedger(
        from_date=from_date,
        to_date=to_date,
        dates=[duty_date.isoformat() for duty_date in dates],
        tag_codes=list(MESS_LEDGER_TAGS),
        rows=rows,
        boro_khana_days=boro_khana_days,
    )
