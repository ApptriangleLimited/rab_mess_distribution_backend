"""Built-in allowance tags — mirror `frontend/src/lib/constants.ts`."""

from decimal import Decimal

BUILTIN_DAILY_TAGS: tuple[str, ...] = (
    "FR",
    "CL",
    "PL",
    "WR",
    "CD",
    "WIT",
    "MED",
    "TRG",
    "MS",
)

RATE_ONLY_TAGS: tuple[str, ...] = ("FUEL", "CLFR")

DEFAULT_BUILTIN_RATES: dict[str, Decimal] = {
    "FR": Decimal("220.00"),
    "CL": Decimal("0.00"),
    "PL": Decimal("0.00"),
    "WR": Decimal("0.00"),
    "CD": Decimal("0.00"),
    "WIT": Decimal("0.00"),
    "MED": Decimal("0.00"),
    "TRG": Decimal("0.00"),
    "MS": Decimal("180.00"),
    "FUEL": Decimal("50.00"),
    "CLFR": Decimal("2500.00"),
}

PROTECTED_RATE_TAGS: frozenset[str] = frozenset(
    {tag.upper() for tag in (*BUILTIN_DAILY_TAGS, *RATE_ONLY_TAGS)}
)

TAG_NAME_RE = r"^[A-Za-z0-9]{2,8}$"


def is_protected_rate_tag(tag: str) -> bool:
    return tag.strip().upper() in PROTECTED_RATE_TAGS


def is_rate_only_tag(tag: str) -> bool:
    return tag.strip().upper() in {value.upper() for value in RATE_ONLY_TAGS}
