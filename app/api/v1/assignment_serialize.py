from datetime import date, datetime, timezone

from app.services.carry import ProjectedCell


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(utc.microsecond / 1000):03d}Z"


def assignment_cell_public(cell: ProjectedCell) -> dict:
    payload = {
        "member_id": cell.member_id,
        "date": cell.date.isoformat(),
        "tag": cell.tag,
        "source": cell.source,
    }
    if cell.updated_at is not None:
        payload["updated_at"] = _iso_z(cell.updated_at)
    if cell.updated_by is not None:
        payload["updated_by"] = cell.updated_by
    return payload


def assignment_summary_public(summary) -> dict:
    return {
        "from": summary.from_date.isoformat(),
        "to": summary.to_date.isoformat(),
        "by_tag": summary.by_tag,
        "total_tagged_person_days": summary.total_tagged_person_days,
        "member_count": summary.member_count,
    }
