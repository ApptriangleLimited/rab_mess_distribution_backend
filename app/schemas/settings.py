from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RateItemIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tag: str = Field(min_length=1)
    amount_per_day: Decimal = Field(ge=0)

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()


class RatesReplaceIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[RateItemIn] = Field(min_length=1)


class RateCreateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tag: str = Field(min_length=2, max_length=8)
    amount_per_day: Decimal = Field(ge=0)

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()


class SenderIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str = Field(min_length=1)
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    routing: str = ""
    branch: str = ""
    branch_location: str = ""
    mapped_tags: list[str] = Field(default_factory=list)
    active: bool = True

    @field_validator("mapped_tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for raw in value:
            tag = raw.strip().upper()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            out.append(tag)
        return out
