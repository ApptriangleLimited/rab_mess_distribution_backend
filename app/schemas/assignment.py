from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentPutIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    member_id: str = Field(min_length=1)
    date: date
    tag: str = Field(min_length=1)

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()


class AssignmentBulkPutIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: date
    tag: str = Field(min_length=1)
    member_ids: list[str] = Field(min_length=1)

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()


class AssignmentRangePutIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    member_id: str = Field(min_length=1)
    dates: list[date] = Field(min_length=1)
    tag: str = ""

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()
