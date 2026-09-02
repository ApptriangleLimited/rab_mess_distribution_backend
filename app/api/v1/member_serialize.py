from datetime import date, datetime, timezone

from app.models.member import Member
from app.models.member_constants import (
    APPROVAL_APPROVED,
    APPROVAL_LEGACY_PENDING,
    APPROVAL_PENDING_CC,
    APPROVAL_PENDING_DAILY,
    PENDING_APPROVAL_STATUSES,
)


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(utc.microsecond / 1000):03d}Z"


def _date_str(value: date | None) -> str | None:
    return value.isoformat() if value else None


def normalize_approval(status: str) -> str:
    """DB may still have `accepted` or legacy `pending`; API uses workflow values."""
    if status == "accepted":
        return APPROVAL_APPROVED
    if status == APPROVAL_LEGACY_PENDING:
        return APPROVAL_PENDING_DAILY
    return status


def approval_db_values(wanted: str) -> tuple[str, ...]:
    """Map API filter to DB values (includes legacy rows)."""
    norm = normalize_approval(wanted)
    if norm == APPROVAL_APPROVED:
        return (APPROVAL_APPROVED, "accepted")
    if norm == APPROVAL_PENDING_CC:
        return (APPROVAL_PENDING_CC,)
    if norm == APPROVAL_PENDING_DAILY:
        return (APPROVAL_PENDING_DAILY, APPROVAL_LEGACY_PENDING)
    if norm == APPROVAL_LEGACY_PENDING or wanted == APPROVAL_LEGACY_PENDING:
        return PENDING_APPROVAL_STATUSES
    return (norm,)


def member_public(member: Member) -> dict:
    return {
        "id": member.id,
        "name": member.name,
        "personal_id": member.personal_id,
        "rab_id": member.rab_id,
        "rfid": member.rfid,
        "rank": member.rank,
        "wing": member.wing,
        "member_type": member.member_type,
        "dropdown_no": member.dropdown_no,
        "phone": member.phone,
        "documents": member.documents or [],
        "status": member.status,
        "approval_status": normalize_approval(member.approval_status),
        "created_via": member.created_via,
        "bank_name": member.bank_name,
        "account_name": member.account_name,
        "account_number": member.account_number,
        "routing": member.routing,
        "branch": member.branch,
        "branch_location": member.branch_location,
        "joining_date": _date_str(member.joining_date) or "",
        "out_date": _date_str(member.out_date) or "",
        "default_tag": (member.default_tag or "MS").strip().upper() or "MS",
        "emergency_contacts": [
            {"name": c.name, "relation": c.relation, "phone": c.phone}
            for c in member.emergency_contacts
        ],
        "created_at": _iso_z(member.created_at),
        "updated_at": _iso_z(member.updated_at),
    }
