from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.member_constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING_DAILY,
    APPROVAL_LEGACY_PENDING,
)


class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    size: int = 0
    url: str | None = None


class EmergencyContactIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    relation: str = ""
    phone: str = ""


class MemberEntryIn(BaseModel):
    """Public member entry. Server forces pending + inactive. No password."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1)
    rab_id: str = Field(min_length=1)
    personal_id: str = ""
    rfid: str = ""
    rank: str = ""
    wing: str = ""
    member_type: Literal["new", "attached", "permanent", "guest", "civilian"] = "permanent"
    dropdown_no: str = ""
    phone: str = ""
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    routing: str = ""
    branch: str = ""
    branch_location: str = ""
    joining_date: date | None = None
    out_date: date | None = None
    default_tag: str = "MS"
    documents: list[DocumentIn] = Field(default_factory=list)
    emergency_contacts: list[EmergencyContactIn] = Field(default_factory=list)

    @field_validator("joining_date", "out_date", mode="before")
    @classmethod
    def empty_date(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name is required")
        return s

    @field_validator("default_tag")
    @classmethod
    def norm_default_tag(cls, v: str) -> str:
        s = (v or "MS").strip().upper()
        return s or "MS"

    @field_validator("rab_id")
    @classmethod
    def norm_rab_id(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("rab_id is required")
        return s


class MemberCreateIn(MemberEntryIn):
    """Staff create — server sets status/approval from staff role."""

    status: Literal["0", "1"] = "1"
    approval_status: Literal[
        "pending_cc",
        "pending_daily",
        "pending",
        "approved",
        "rejected",
        "ended",
    ] = APPROVAL_PENDING_DAILY

    @field_validator("approval_status", mode="before")
    @classmethod
    def fold_accepted(cls, v: object) -> object:
        if v == "accepted":
            return APPROVAL_APPROVED
        if v == APPROVAL_LEGACY_PENDING:
            return APPROVAL_PENDING_DAILY
        return v
