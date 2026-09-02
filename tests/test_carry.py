from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.allowance_rate import AllowanceRate
from app.models.daily import DailyAssignment, SuppressedCarry
from app.models.member import Member
from app.models.member_constants import APPROVAL_APPROVED, CREATED_VIA_DAILY
from app.services.carry import (
    find_prior_stored_tag,
    project_assignments,
    summarize_assignments,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _insert_member(
    db,
    *,
    rab_id: str,
    out_date: date | None = None,
    default_tag: str = "MS",
) -> Member:
    db.query(Member).filter(Member.rab_id == rab_id).delete()
    member = Member(
        name="Carry Test",
        rab_id=rab_id,
        status="1",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
        out_date=out_date,
        default_tag=default_tag,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def test_find_prior_stored_tag_walks_back(create_schema):
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-CARRY-1")
    stored = {
        (member.id, date(2026, 8, 10)): DailyAssignment(
            member_id=member.id,
            date=date(2026, 8, 10),
            tag="MS",
            updated_at=_utcnow(),
        )
    }
    assert find_prior_stored_tag(stored, member.id, date(2026, 8, 12)) == "MS"
    assert find_prior_stored_tag(stored, member.id, date(2026, 8, 10)) is None
    db.close()


def test_project_uses_default_tag_not_last_paint(create_schema):
    """Default FR; paint CL; empty days after resume FR (not carry CL)."""
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-CARRY-2", default_tag="FR")
    d1 = date(2026, 8, 10)
    d2 = date(2026, 8, 11)
    d3 = date(2026, 8, 12)
    d4 = date(2026, 8, 13)

    db.add(
        DailyAssignment(
            member_id=member.id,
            date=d1,
            tag="CL",
            updated_at=_utcnow(),
        )
    )
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=d2,
            tag="CL",
            updated_at=_utcnow(),
        )
    )
    db.add(SuppressedCarry(member_id=member.id, date=d3))
    db.commit()

    cells = project_assignments(db, from_date=d1, to_date=d4, member_id=member.id)
    by_date = {cell.date: cell for cell in cells}

    assert by_date[d1].source == "stored"
    assert by_date[d1].tag == "CL"
    assert by_date[d2].source == "stored"
    assert by_date[d2].tag == "CL"
    assert by_date[d3].source == "suppressed"
    assert by_date[d3].tag is None
    assert by_date[d4].source == "carry"
    assert by_date[d4].tag == "FR"
    db.close()


def test_summary_counts_projected_tags(create_schema):
    db = SessionLocal()
    member = _insert_member(db, rab_id="RAB-CARRY-3", default_tag="MS")
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=date(2026, 8, 1),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()

    summary = summarize_assignments(
        db,
        from_date=date(2026, 8, 1),
        to_date=date(2026, 8, 3),
        member_id=member.id,
    )
    assert summary.by_tag["MS"] == 3
    assert summary.total_tagged_person_days == 3
    assert summary.member_count == 1
    db.close()


def test_member_after_out_date_projects_empty(create_schema):
    db = SessionLocal()
    member = _insert_member(
        db,
        rab_id="RAB-CARRY-4",
        out_date=date(2026, 8, 10),
        default_tag="MS",
    )
    db.add(
        DailyAssignment(
            member_id=member.id,
            date=date(2026, 8, 9),
            tag="MS",
            updated_at=_utcnow(),
        )
    )
    db.commit()

    cells = project_assignments(
        db,
        from_date=date(2026, 8, 9),
        to_date=date(2026, 8, 11),
        member_id=member.id,
    )
    by_date = {cell.date: cell for cell in cells}
    assert by_date[date(2026, 8, 9)].source == "stored"
    # out_date inclusive: can_assign on out_date, empty after
    assert by_date[date(2026, 8, 10)].source == "carry"
    assert by_date[date(2026, 8, 10)].tag == "MS"
    assert by_date[date(2026, 8, 11)].source == "empty"
    db.close()


def test_seed_builtin_rates(create_schema):
    db = SessionLocal()
    db.query(AllowanceRate).delete()
    db.commit()
    from app.services.carry import seed_builtin_rates

    created = seed_builtin_rates(db)
    db.commit()
    assert created == 11
    assert db.get(AllowanceRate, "MS") is not None
    assert db.get(AllowanceRate, "FUEL") is not None
    db.close()
