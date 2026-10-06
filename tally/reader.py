"""Reads bank statement CSV exports.

Every bank names its columns differently, so instead of expecting one exact
format, the reader looks for known names for each column it needs. Statements
come in two shapes: separate Debit and Credit columns, or a single signed
Amount column. Both are supported.
"""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction

DATE_COLUMNS = ("date", "trans. date", "transaction date", "trans date", "posted date", "value date")
DESCRIPTION_COLUMNS = ("narration", "description", "details", "remarks", "transaction details")
DEBIT_COLUMNS = ("debit", "debits", "withdrawal", "withdrawals", "money out", "dr")
CREDIT_COLUMNS = ("credit", "credits", "deposit", "deposits", "lodgement", "money in", "cr")
AMOUNT_COLUMNS = ("amount", "amount (ngn)", "value")

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%d %b %Y", "%d-%b-%y")


class StatementError(Exception):
    """Raised when a file cannot be read as a statement."""


def _find_column(headers: list[str], options: tuple[str, ...]) -> str | None:
    normalised = {h.strip().lower(): h for h in headers}
    for option in options:
        if option in normalised:
            return normalised[option]
    return None


def parse_date(text: str) -> date:
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date: {text!r}")


def parse_amount(text: str | None) -> Decimal:
    """Turns '1,250.00', '-500', '(500.00)' or '' into a Decimal."""
    if text is None:
        return Decimal("0")

    clean = text.strip().replace(",", "").replace("₦", "").replace("NGN", "").strip()
    if clean in ("", "-"):
        return Decimal("0")

    # some banks write negative numbers in brackets, accounting style
    negative = clean.startswith("(") and clean.endswith(")")
    if negative:
        clean = clean[1:-1]

    try:
        value = Decimal(clean)
    except InvalidOperation:
        raise ValueError(f"unrecognised amount: {text!r}") from None

    return -value if negative else value


def read_statement(path: Path) -> list[Transaction]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        raise StatementError(f"{path} does not exist") from None
    except UnicodeDecodeError:
        raise StatementError(f"{path} is not a text CSV file") from None

    date_col = _find_column(headers, DATE_COLUMNS)
    desc_col = _find_column(headers, DESCRIPTION_COLUMNS)
    debit_col = _find_column(headers, DEBIT_COLUMNS)
    credit_col = _find_column(headers, CREDIT_COLUMNS)
    amount_col = _find_column(headers, AMOUNT_COLUMNS)

    if not date_col or not desc_col:
        raise StatementError(
            f"could not find a date and a description column in {path.name}. "
            f"Columns found: {', '.join(headers) or 'none'}"
        )
    if not amount_col and not (debit_col or credit_col):
        raise StatementError(f"could not find an amount, debit or credit column in {path.name}")

    transactions = []
    # start=2 because line 1 is the header, so error messages match the file
    for line_number, row in enumerate(rows, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue  # blank line, common at the end of exports

        try:
            day = parse_date(row[date_col])
            if amount_col:
                amount = parse_amount(row[amount_col])
            else:
                debit = parse_amount(row.get(debit_col)) if debit_col else Decimal("0")
                credit = parse_amount(row.get(credit_col)) if credit_col else Decimal("0")
                amount = credit - abs(debit)
        except ValueError as error:
            raise StatementError(f"line {line_number}: {error}") from None

        if amount == 0:
            continue

        description = " ".join(row[desc_col].split())  # collapse repeated spaces
        transactions.append(Transaction(day=day, description=description, amount=amount))

    return transactions
