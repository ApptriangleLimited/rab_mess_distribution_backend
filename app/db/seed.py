"""Idempotent demo seed for `users` + `members`. From backend/: python -m app.db.seed"""

from __future__ import annotations

from datetime import date

from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.member import Member, MemberEmergencyContact
from app.models.member_constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING_CC,
    APPROVAL_PENDING_DAILY,
    APPROVAL_REJECTED,
    CREATED_VIA_CC,
    CREATED_VIA_DAILY,
    CREATED_VIA_PUBLIC,
)
from app.models.staff import ROLES, StaffAccount
from app.services.carry import seed_builtin_rates

# Match frontend Manpower demo grid (seed.ts SEED_WINGS × SEED_RANK_PER_WING).
_MEMBER_BANKS = ("Trust bank", "Community bank", "Sonali Bank")
_BANK_BRANCHES = ("Mirpur", "Uttara", "Motijheel")
_BANK_LOCATIONS = ("Dhaka", "Dhaka", "Dhaka")

_ROLE_NAMES = {
    "cc": "CC Desk",
    "daily": "Daily Desk",
    "mess": "Mess Desk",
    "consume": "Consume Desk",
    "ration": "Ration Desk",
    "admin": "Admin",
}

_FIRST = (
    "Karim",
    "Nusrat",
    "Rafiq",
    "Sabbir",
    "Imran",
    "Farhana",
    "Jamal",
    "Tania",
    "Hasan",
    "Shila",
    "Mehedi",
    "Rina",
    "Omar",
    "Lamia",
    "Sajjad",
    "Ayesha",
    "Babul",
    "Nazmul",
    "Sumaiya",
    "Arif",
    "Farzana",
    "Kamal",
    "Nadia",
    "Rubel",
    "Popy",
)
_LAST = (
    "Hossain",
    "Jahan",
    "Ahmed",
    "Khan",
    "Ali",
    "Akter",
    "Uddin",
    "Rahman",
    "Mahmud",
    "Begum",
    "Hasan",
    "Faruk",
    "Chowdhury",
    "Sultana",
    "Mia",
    "Islam",
)

# Wing × rank grid for Manpower Form 1 (non-zero প্রাপ্ত).
_SEED_WINGS = (
    "Admin",
    "Ops Wg",
    "Int Wg",
    "Comm & MIS Wg",
    "Trg Wg",
    "L & M Wg",
    "Inv Wg",
    "Air Wg",
    "R & D Cell",
    "Training School",
)
_SEED_RANK_PER_WING: dict[str, int] = {
    "Officer": 2,
    "DAD": 2,
    "RT": 1,
    "ASI": 3,
    "AASI": 3,
    "Naik": 4,
    "Constable": 7,
    "Cook": 1,
    "ANCE": 1,
    "Civill": 1,
    "Attached": 1,
}
_CONTACT_NAMES = ("Nusrat", "Fatema", "Rahim", "Salma")
_RELATIONS = ("spouse", "father", "mother", "brother")


def _member_type_for_rank(rank: str) -> str:
    if rank == "Civill":
        return "civilian"
    if rank == "Attached":
        return "attached"
    return "permanent"


def _member_rows() -> list[dict]:
    """Demo roster: edge cases + fat wing×rank grid for Manpower."""
    rows: list[dict] = []
    i = 0

    def add(
        *,
        rank: str,
        wing: str,
        member_type: str,
        approval_status: str,
        created_via: str,
        status: str,
    ) -> None:
        nonlocal i
        i += 1
        n = f"{i:03d}"
        is_civilian = member_type == "civilian" or rank == "Civill"
        is_new = member_type == "new"
        bank = _MEMBER_BANKS[(i - 1) % len(_MEMBER_BANKS)]
        bank_branch = _BANK_BRANCHES[(i - 1) % len(_BANK_BRANCHES)]
        bank_location = _BANK_LOCATIONS[(i - 1) % len(_BANK_LOCATIONS)]
        name = f"{_FIRST[(i - 1) % len(_FIRST)]} {_LAST[(i - 1) % len(_LAST)]}"
        rows.append(
            {
                "name": name,
                "personal_id": f"PID-SEED-{n}",
                "rab_id": f"RAB-SEED-{n}",
                "rfid": "" if is_civilian else f"RFID-SEED-{n}",
                "rank": "Civill" if is_civilian else ("" if is_new else rank),
                "wing": "" if is_new else wing,
                "member_type": member_type,
                "dropdown_no": "" if is_new else str((i % 40) + 1),
                "phone": f"0171{i:07d}"[-11:],
                "status": status,
                "approval_status": approval_status,
                "created_via": created_via,
                "bank_name": bank,
                "account_name": name,
                "account_number": (
                    f"{'11' if approval_status != APPROVAL_APPROVED else '22'}02{i:06d}"
                ),
                "routing": f"20027{i:04d}",
                "branch": bank_branch,
                "branch_location": bank_location,
                "joining_date": None
                if is_new
                else date(2023 + (i % 3), ((i - 1) % 12) + 1, ((i - 1) % 28) + 1),
                "contacts": (
                    (
                        _CONTACT_NAMES[(i - 1) % len(_CONTACT_NAMES)],
                        _RELATIONS[(i - 1) % len(_RELATIONS)],
                        f"0181{i:07d}"[-11:],
                    ),
                )
                if i % 2 == 1
                else (),
            }
        )

    # Edge cases for approval queues / inactive (not Manpower held).
    add(
        rank="Constable",
        wing="Ops Wg",
        member_type="new",
        approval_status=APPROVAL_PENDING_CC,
        created_via=CREATED_VIA_PUBLIC,
        status="0",
    )
    add(
        rank="ASI",
        wing="Int Wg",
        member_type="permanent",
        approval_status=APPROVAL_PENDING_DAILY,
        created_via=CREATED_VIA_CC,
        status="0",
    )
    add(
        rank="DAD",
        wing="Admin",
        member_type="permanent",
        approval_status=APPROVAL_APPROVED,
        created_via=CREATED_VIA_DAILY,
        status="0",
    )

    for wing in _SEED_WINGS:
        for rank, copies in _SEED_RANK_PER_WING.items():
            for _ in range(copies):
                add(
                    rank=rank,
                    wing=wing,
                    member_type=_member_type_for_rank(rank),
                    approval_status=APPROVAL_APPROVED,
                    created_via=CREATED_VIA_CC,
                    status="1",
                )

    # Pending civilian for CC queue.
    add(
        rank="Civill",
        wing="Admin",
        member_type="civilian",
        approval_status=APPROVAL_PENDING_CC,
        created_via=CREATED_VIA_PUBLIC,
        status="1",
    )

    # Sparse rejected samples.
    if rows:
        for idx in range(16, len(rows), 47):
            rows[idx]["approval_status"] = APPROVAL_REJECTED
            rows[idx]["status"] = "0"
            rows[idx]["created_via"] = CREATED_VIA_CC

    return rows


def seed_users(db: Session) -> int:
    created = 0
    password_hash = hash_password(settings.seed_staff_password)
    for role in ROLES:
        email = f"{role}@mess.rab"
        old = f"{role}@mess.local"
        row = (
            db.query(StaffAccount)
            .filter(StaffAccount.email.in_((email, old)))
            .one_or_none()
        )
        if row is not None:
            if row.email != email:
                row.email = email
            continue
        db.add(
            StaffAccount(
                email=email,
                password_hash=password_hash,
                display_name=_ROLE_NAMES[role],
                role=role,
                is_active=True,
            )
        )
        created += 1
    return created


def backfill_member_approval(db: Session) -> int:
    """Refresh demo seed rows + legacy pending/accepted after migration 005."""
    updated = 0
    by_rab = {row["rab_id"]: row for row in _member_rows()}
    for member in db.query(Member).all():
        changed = False
        seed_row = by_rab.get(member.rab_id)
        if seed_row:
            for field in (
                "approval_status",
                "created_via",
                "status",
                "rank",
                "wing",
                "member_type",
                "name",
            ):
                if getattr(member, field) != seed_row[field]:
                    setattr(member, field, seed_row[field])
                    changed = True
        else:
            if member.approval_status == "pending":
                member.approval_status = APPROVAL_PENDING_DAILY
                changed = True
            elif member.approval_status == "accepted":
                member.approval_status = APPROVAL_APPROVED
                changed = True
            if not member.created_via:
                member.created_via = CREATED_VIA_CC
                changed = True
        if changed:
            updated += 1
    return updated


def seed_members(db: Session) -> int:
    created = 0
    existing_ids = {r[0] for r in db.query(Member.rab_id).all()}
    by_rab = {
        m.rab_id: m
        for m in db.query(Member).filter(Member.rab_id.like("RAB-SEED-%")).all()
    }
    for row in _member_rows():
        rab_id = row["rab_id"]
        if rab_id in by_rab:
            member = by_rab[rab_id]
            for field in (
                "name",
                "personal_id",
                "rfid",
                "rank",
                "wing",
                "member_type",
                "dropdown_no",
                "phone",
                "status",
                "approval_status",
                "created_via",
                "bank_name",
                "account_name",
                "account_number",
                "routing",
                "branch",
                "branch_location",
                "joining_date",
            ):
                setattr(member, field, row[field])
            continue
        if rab_id in existing_ids:
            continue
        member = Member(
            name=row["name"],
            personal_id=row["personal_id"],
            rab_id=rab_id,
            rfid=row["rfid"],
            rank=row["rank"],
            wing=row["wing"],
            member_type=row["member_type"],
            dropdown_no=row["dropdown_no"],
            phone=row["phone"],
            status=row["status"],
            approval_status=row["approval_status"],
            created_via=row["created_via"],
            bank_name=row["bank_name"],
            account_name=row["account_name"],
            account_number=row["account_number"],
            routing=row["routing"],
            branch=row["branch"],
            branch_location=row["branch_location"],
            joining_date=row["joining_date"],
            emergency_contacts=[
                MemberEmergencyContact(name=n, relation=rel, phone=ph)
                for n, rel, ph in row["contacts"]
            ],
        )
        db.add(member)
        created += 1
    return created


def seed_allowance_rates(db: Session) -> int:
    return seed_builtin_rates(db)


def run() -> None:
    url = make_url(settings.database_url)
    db = SessionLocal()
    try:
        users_n = seed_users(db)
        members_n = seed_members(db)
        rates_n = seed_allowance_rates(db)
        backfill_n = backfill_member_approval(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(
        f"Seeded {url.database}: users +{users_n}, members +{members_n}, "
        f"rates +{rates_n}, backfill {backfill_n}"
    )


if __name__ == "__main__":
    run()
