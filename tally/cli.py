import argparse
import sys
from pathlib import Path

from .reader import StatementError, read_statement
from .report import render_list, render_month, summarise, write_csv
from .rules import UNCATEGORISED, categorise_all, load_rules

DEFAULT_RULES = Path(__file__).parent / "default_rules.json"


def month_arg(text: str) -> str:
    parts = text.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or not all(p.isdigit() for p in parts) or not 1 <= int(parts[1]) <= 12:
        raise argparse.ArgumentTypeError(f"expected a month like 2026-09, got {text!r}")
    return f"{parts[0]}-{int(parts[1]):02d}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tally",
        description="Sort a bank statement CSV into spending categories and show a monthly summary.",
    )
    parser.add_argument("statement", type=Path, help="CSV file exported from your bank")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES, help="JSON file of category keywords")
    parser.add_argument("--month", type=month_arg, help="only show this month, for example 2026-09")
    parser.add_argument(
        "--uncategorised",
        action="store_true",
        help="list the spending no rule matched, so you can add keywords for it",
    )
    parser.add_argument("--category", help="list every transaction in one category")
    parser.add_argument("--export", type=Path, metavar="PATH", help="also save the categorised transactions as CSV")
    parser.add_argument("--currency", default="₦", help="symbol to print in front of amounts (default: ₦)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        rules = load_rules(args.rules)
        transactions = categorise_all(read_statement(args.statement), rules)
    except (StatementError, ValueError) as error:
        print(f"tally: {error}", file=sys.stderr)
        return 1

    if args.month:
        transactions = [t for t in transactions if t.month == args.month]
        if not transactions:
            print(f"tally: no transactions in {args.month}", file=sys.stderr)
            return 1

    if args.uncategorised or args.category:
        wanted = UNCATEGORISED if args.uncategorised else args.category
        matches = [t for t in transactions if (t.category or "").lower() == wanted.lower()]
        print(render_list(matches, args.currency))
    else:
        summaries = summarise(transactions)
        print("\n\n\n".join(render_month(s, args.currency) for s in summaries))

    if args.export:
        write_csv(transactions, args.export)
        print(f"\nSaved {len(transactions)} transactions to {args.export}")

    return 0
