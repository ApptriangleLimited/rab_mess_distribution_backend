from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, JSON, String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.member_constants import CREATED_VIA_CC, APPROVAL_PENDING_DAILY


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    personal_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    rab_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    rfid: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    rank: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    wing: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    member_type: Mapped[str] = mapped_column(String(16), nullable=False, default="permanent")
    dropdown_no: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(1), nullable=False, default="0")
    approval_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=APPROVAL_PENDING_DAILY
    )
    created_via: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CREATED_VIA_CC
    )
    bank_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    account_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    account_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    routing: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    branch: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    branch_location: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    default_tag: Mapped[str] = mapped_column(String(16), nullable=False, default="MS")
    documents: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    emergency_contacts: Mapped[list["MemberEmergencyContact"]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
    )


class MemberEmergencyContact(Base):
    __tablename__ = "member_emergency_contacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    relation: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    member: Mapped[Member] = relationship(back_populates="emergency_contacts")
