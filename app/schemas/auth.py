from pydantic import BaseModel, ConfigDict, Field, field_validator


def _fold_email(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value.strip().lower()
    if "@" not in text or text.startswith("@") or text.endswith("@"):
        raise ValueError("Invalid email")
    local, _, domain = text.partition("@")
    if not local or "." not in domain:
        raise ValueError("Invalid email")
    return text


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def fold_email(cls, value: object) -> object:
        return _fold_email(value)


class StaffOut(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
