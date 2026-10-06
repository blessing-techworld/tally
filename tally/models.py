from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """One line from a bank statement.

    `amount` is negative for money going out and positive for money coming in,
    so totals are a plain sum.
    """

    day: date
    description: str
    amount: Decimal
    category: str | None = None

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def month(self) -> str:
        return self.day.strftime("%Y-%m")

    def with_category(self, category: str | None) -> "Transaction":
        return replace(self, category=category)
