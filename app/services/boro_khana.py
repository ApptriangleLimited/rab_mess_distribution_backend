"""Boro Khana day flags — see docs/BORO_KHANA_PLAN.md."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.daily import BoroKhanaDate
from app.models.staff import StaffAccount
from app.services.assignments import require_daily_writer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_boro_khana(db: Session, duty_date: date) -> bool:
    return db.get(BoroKhanaDate, duty_date) is not None


def list_boro_khana_dates(db: Session, from_date: date, to_date: date) -> list[str]:
    rows = (
        db.query(BoroKhanaDate.date)
        .filter(BoroKhanaDate.date >= from_date, BoroKhanaDate.date <= to_date)
        .order_by(BoroKhanaDate.date.asc())
        .all()
    )
    return [row[0].isoformat() for row in rows]


def set_boro_khana(
    db: Session,
    staff: StaffAccount,
    duty_date: date,
    *,
    on: bool,
) -> dict:
    require_daily_writer(staff)
    existing = db.get(BoroKhanaDate, duty_date)
    if on:
        if existing is None:
            db.add(
                BoroKhanaDate(
                    date=duty_date,
                    set_by=staff.id,
                    set_at=_utcnow(),
                )
            )
    elif existing is not None:
        db.delete(existing)
    db.flush()
    return {"date": duty_date.isoformat(), "on": on}
