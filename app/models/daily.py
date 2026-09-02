from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DailyAssignment(Base):
    __tablename__ = "daily_assignments"
    __table_args__ = (
        UniqueConstraint("member_id", "date", name="uq_daily_assignments_member_date"),
        Index("ix_daily_assignments_date", "date"),
        Index("ix_daily_assignments_member_date", "member_id", "date"),
        Index("ix_daily_assignments_date_tag", "date", "tag"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    tag: Mapped[str] = mapped_column(String(16), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow
    )


class ApprovedDate(Base):
    __tablename__ = "approved_dates"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    approved_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow
    )


class SuppressedCarry(Base):
    __tablename__ = "suppressed_carries"
    __table_args__ = (Index("ix_suppressed_carries_date", "date"),)

    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)


class BoroKhanaDate(Base):
    __tablename__ = "boro_khana_dates"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    set_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    set_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow
    )
