"""Sender payout accounts + tag map — see BACKEND_PLAN.md §3."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SenderAccount(Base):
    __tablename__ = "sender_accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    account_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    account_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    routing: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    branch: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    branch_location: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    tag_maps: Mapped[list["SenderTagMap"]] = relationship(
        "SenderTagMap",
        back_populates="sender",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SenderTagMap(Base):
    __tablename__ = "sender_tag_map"
    __table_args__ = (
        UniqueConstraint("sender_id", "tag", name="uq_sender_tag_map_sender_tag"),
    )

    sender_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sender_accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(16), primary_key=True)

    sender: Mapped[SenderAccount] = relationship(
        "SenderAccount", back_populates="tag_maps"
    )
