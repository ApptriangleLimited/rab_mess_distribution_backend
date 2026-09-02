"""Sender payout accounts — port of `frontend/src/lib/store/senders.ts`."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.sender import SenderAccount, SenderTagMap
from app.models.staff import StaffAccount
from app.services.settings_rates import require_settings_writer


def sender_public(sender: SenderAccount) -> dict:
    tags = sorted({row.tag for row in sender.tag_maps})
    return {
        "id": sender.id,
        "label": sender.label,
        "bank_name": sender.bank_name,
        "account_name": sender.account_name,
        "account_number": sender.account_number,
        "routing": sender.routing,
        "branch": sender.branch,
        "branch_location": sender.branch_location,
        "mapped_tags": tags,
        "active": sender.active,
    }


def list_senders(db: Session) -> list[SenderAccount]:
    return (
        db.query(SenderAccount)
        .order_by(SenderAccount.label.asc())
        .all()
    )


def get_sender(db: Session, sender_id: str) -> SenderAccount:
    sender = db.get(SenderAccount, sender_id)
    if sender is None:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Sender account not found.",
            errors=[
                {
                    "field": "id",
                    "code": "NOT_FOUND",
                    "message": "Sender account not found.",
                }
            ],
        )
    return sender


def _normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in tags:
        tag = raw.strip().upper()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append(tag)
    return out


def _set_sender_tags(sender: SenderAccount, tags: list[str]) -> None:
    wanted = _normalize_tags(tags)
    current = {row.tag: row for row in sender.tag_maps}
    for tag, row in list(current.items()):
        if tag not in wanted:
            sender.tag_maps.remove(row)
    for tag in wanted:
        if tag not in current:
            sender.tag_maps.append(SenderTagMap(sender_id=sender.id, tag=tag))


def create_sender(
    db: Session,
    staff: StaffAccount,
    *,
    label: str,
    bank_name: str,
    account_name: str,
    account_number: str,
    routing: str,
    branch: str,
    branch_location: str,
    mapped_tags: list[str],
    active: bool = True,
) -> SenderAccount:
    require_settings_writer(staff)
    if not label.strip():
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Sender label is required.",
            errors=[
                {
                    "field": "label",
                    "code": "REQUIRED",
                    "message": "Sender label is required.",
                }
            ],
        )
    sender = SenderAccount(
        label=label.strip(),
        bank_name=bank_name.strip(),
        account_name=account_name.strip(),
        account_number=account_number.strip(),
        routing=routing.strip(),
        branch=branch.strip(),
        branch_location=branch_location.strip(),
        active=active,
    )
    db.add(sender)
    db.flush()
    _set_sender_tags(sender, mapped_tags)
    db.flush()
    return sender


def update_sender(
    db: Session,
    staff: StaffAccount,
    sender_id: str,
    *,
    label: str,
    bank_name: str,
    account_name: str,
    account_number: str,
    routing: str,
    branch: str,
    branch_location: str,
    mapped_tags: list[str],
    active: bool = True,
) -> SenderAccount:
    require_settings_writer(staff)
    sender = get_sender(db, sender_id)
    if not label.strip():
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Sender label is required.",
            errors=[
                {
                    "field": "label",
                    "code": "REQUIRED",
                    "message": "Sender label is required.",
                }
            ],
        )
    sender.label = label.strip()
    sender.bank_name = bank_name.strip()
    sender.account_name = account_name.strip()
    sender.account_number = account_number.strip()
    sender.routing = routing.strip()
    sender.branch = branch.strip()
    sender.branch_location = branch_location.strip()
    sender.active = active
    _set_sender_tags(sender, mapped_tags)
    db.flush()
    return sender


def delete_sender(db: Session, staff: StaffAccount, sender_id: str) -> None:
    require_settings_writer(staff)
    sender = get_sender(db, sender_id)
    db.delete(sender)
