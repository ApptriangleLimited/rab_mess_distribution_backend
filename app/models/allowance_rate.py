from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AllowanceRate(Base):
    __tablename__ = "allowance_rates"

    tag: Mapped[str] = mapped_column(String(16), primary_key=True)
    amount_per_day: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
