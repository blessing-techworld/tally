import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Transaction

BAR_WIDTH = 24


@dataclass(frozen=True)
class MonthSummary:
    month: str  # "2026-09"
    money_in: Decimal
    money_out: Decimal  # stored as a positive number
    spending: list[tuple[str, Decimal]]  # biggest category first

    @property
    def left_over(self) -> Decimal:
        return self.money_in - self.money_out

    @property
    def title(self) -> str:
        year, month = map(int, self.month.split("-"))
        return date(year, month, 1).strftime("%B %Y")


def summarise(transactions: list[Transaction]) -> list[MonthSummary]:
    by_month: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        by_month[t.month].append(t)

    summaries = []
    for month in sorted(by_month):
        items = by_month[month]
        money_in = sum((t.amount for t in items if t.is_income), Decimal("0"))

        spending: dict[str, Decimal] = defaultdict(Decimal)
        for t in items:
            if not t.is_income:
                spending[t.category or "Uncategorised"] += -t.amount

        ranked = sorted(spending.items(), key=lambda pair: pair[1], reverse=True)
        summaries.append(MonthSummary(month, money_in, sum(spending.values(), Decimal("0")), ranked))

    return summaries


def format_money(value: Decimal, symbol: str = "₦") -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{symbol}{abs(value):,.2f}"


def _bar(share: float) -> str:
    if share <= 0:
        return ""
    return "█" * max(1, round(share * BAR_WIDTH))


def render_month(summary: MonthSummary, symbol: str = "₦") -> str:
    money = [format_money(v, symbol) for v in (summary.money_in, summary.money_out, summary.left_over)]
    amount_width = max(len(m) for m in money)
    if summary.spending:
        amount_width = max(amount_width, *(len(format_money(v, symbol)) for _, v in summary.spending))
    name_width = max([len("Left over"), *(len(name) for name, _ in summary.spending)])

    lines = [summary.title, "=" * len(summary.title), ""]
    for label, value in zip(("Money in", "Money out", "Left over"), money):
        lines.append(f"  {label:<{name_width}}  {value:>{amount_width}}")

    if summary.spending:
        lines += ["", "  Spending by category", ""]
        for name, value in summary.spending:
            share = float(value / summary.money_out) if summary.money_out else 0
            amount = format_money(value, symbol)
            lines.append(f"  {name:<{name_width}}  {amount:>{amount_width}}  {share:>4.0%}  {_bar(share)}")

    return "\n".join(lines)


def render_list(transactions: list[Transaction], symbol: str = "₦") -> str:
    if not transactions:
        return "Nothing to show."

    amounts = [format_money(t.amount, symbol) for t in transactions]
    width = max(len(a) for a in amounts)
    return "\n".join(
        f"  {t.day.isoformat()}  {a:>{width}}  {t.description}"
        for t, a in zip(transactions, amounts)
    )


def write_csv(transactions: list[Transaction], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "description", "amount", "category"])
        for t in transactions:
            writer.writerow([t.day.isoformat(), t.description, f"{t.amount:.2f}", t.category or ""])

