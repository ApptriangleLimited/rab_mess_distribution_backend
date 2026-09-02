"""ISO date helpers for daily cockpit."""

from __future__ import annotations

from datetime import date, timedelta


def previous_date(value: date) -> date:
    return value - timedelta(days=1)


def each_date(from_date: date, to_date: date) -> list[date]:
    start, end = (from_date, to_date) if from_date <= to_date else (to_date, from_date)
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def month_bounds(month: str) -> tuple[date, date]:
    year_s, month_s = month.split("-", 1)
    year = int(year_s)
    month_num = int(month_s)
    from_date = date(year, month_num, 1)
    if month_num == 12:
        to_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        to_date = date(year, month_num + 1, 1) - timedelta(days=1)
    return from_date, to_date


def extend_back(value: date, days: int) -> date:
    return value - timedelta(days=days)
