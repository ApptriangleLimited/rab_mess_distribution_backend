"""Allowance rate settings — port of `frontend/src/lib/store/rates.ts`."""

from __future__ import annotations

import re
from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants.allowance import (
    DEFAULT_BUILTIN_RATES,
    RATE_ONLY_TAGS,
    TAG_NAME_RE,
    is_protected_rate_tag,
)
from app.core.errors import ApiError
from app.models.allowance_rate import AllowanceRate
from app.models.sender import SenderTagMap
from app.models.staff import StaffAccount
from app.services.carry import seed_builtin_rates

_SETTINGS_WRITE_ROLES = frozenset({"ration", "admin"})


def require_settings_writer(staff: StaffAccount) -> None:
    if staff.role not in _SETTINGS_WRITE_ROLES:
        raise ApiError(
            code="AUTH_UNAUTHORIZED",
            status=403,
            detail="This role cannot edit settings.",
        )


def _normalize_tag(tag: str) -> str:
    return tag.strip().upper()


def _money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def list_rates(db: Session) -> list[AllowanceRate]:
    seed_builtin_rates(db)
    db.flush()
    return db.query(AllowanceRate).order_by(AllowanceRate.tag.asc()).all()


def rate_public(rate: AllowanceRate) -> dict:
    return {
        "tag": rate.tag,
        "amount_per_day": float(rate.amount_per_day),
        "is_builtin": bool(rate.is_builtin),
        "is_protected": is_protected_rate_tag(rate.tag),
    }


def replace_rate_amounts(
    db: Session,
    staff: StaffAccount,
    items: list[dict],
) -> list[AllowanceRate]:
    require_settings_writer(staff)
    rates = {rate.tag: rate for rate in list_rates(db)}
    if not rates:
        raise ApiError(
            code="INTERNAL_ERROR",
            status=500,
            detail="Allowance rates are not seeded.",
        )

    for item in items:
        tag = _normalize_tag(str(item["tag"]))
        if tag not in rates:
            raise ApiError(
                code="VALIDATION_ERROR",
                status=422,
                detail="Unknown allowance tag.",
                errors=[
                    {
                        "field": "tag",
                        "code": "UNKNOWN_TAG",
                        "message": f"Tag {tag} is not configured.",
                    }
                ],
            )
        amount = _money(item["amount_per_day"])
        if amount < 0:
            raise ApiError(
                code="VALIDATION_ERROR",
                status=422,
                detail="Amount must be zero or positive.",
                errors=[
                    {
                        "field": "amount_per_day",
                        "code": "MIN_VALUE",
                        "message": "Amount must be zero or positive.",
                    }
                ],
            )
        rates[tag].amount_per_day = amount

    for only_tag in RATE_ONLY_TAGS:
        key = only_tag.upper()
        if key not in rates:
            db.add(
                AllowanceRate(
                    tag=key,
                    amount_per_day=DEFAULT_BUILTIN_RATES[key],
                    is_builtin=True,
                )
            )

    db.flush()
    return list_rates(db)


def add_custom_rate(
    db: Session,
    staff: StaffAccount,
    *,
    tag: str,
    amount_per_day: Decimal | float | int | str,
) -> AllowanceRate:
    require_settings_writer(staff)
    normalized = _normalize_tag(tag)
    if not re.fullmatch(TAG_NAME_RE, normalized):
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Invalid allowance tag code.",
            errors=[
                {
                    "field": "tag",
                    "code": "INVALID_FORMAT",
                    "message": "Use 2–8 letters or digits.",
                }
            ],
        )
    existing = db.get(AllowanceRate, normalized)
    if existing is not None:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Allowance tag already exists.",
            errors=[
                {
                    "field": "tag",
                    "code": "DUPLICATE",
                    "message": "Allowance tag already exists.",
                }
            ],
        )
    amount = _money(amount_per_day)
    if amount < 0:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Amount must be zero or positive.",
            errors=[
                {
                    "field": "amount_per_day",
                    "code": "MIN_VALUE",
                    "message": "Amount must be zero or positive.",
                }
            ],
        )
    rate = AllowanceRate(
        tag=normalized,
        amount_per_day=amount,
        is_builtin=False,
    )
    db.add(rate)
    db.flush()
    return rate


def delete_custom_rate(db: Session, staff: StaffAccount, tag: str) -> None:
    require_settings_writer(staff)
    normalized = _normalize_tag(tag)
    if is_protected_rate_tag(normalized):
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Built-in allowance tags cannot be deleted.",
            errors=[
                {
                    "field": "tag",
                    "code": "PROTECTED",
                    "message": "Built-in allowance tags cannot be deleted.",
                }
            ],
        )
    rate = db.get(AllowanceRate, normalized)
    if rate is None:
        raise ApiError(
            code="VALIDATION_ERROR",
            status=422,
            detail="Allowance tag not found.",
            errors=[
                {
                    "field": "tag",
                    "code": "NOT_FOUND",
                    "message": "Allowance tag not found.",
                }
            ],
        )
    db.query(SenderTagMap).filter(SenderTagMap.tag == normalized).delete(
        synchronize_session=False
    )
    db.delete(rate)
