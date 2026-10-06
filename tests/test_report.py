import unittest
from datetime import date
from decimal import Decimal

from tally.models import Transaction
from tally.report import format_money, render_month, summarise


def tx(day: int, amount: str, category: str, month: int = 9) -> Transaction:
    return Transaction(date(2026, month, day), "x", Decimal(amount), category)


class SummariseTests(unittest.TestCase):
    def test_totals_per_month(self):
        summaries = summarise([
            tx(1, "1000", "Income"),
            tx(2, "-300", "Food"),
            tx(3, "-200", "Food"),
            tx(4, "-100", "Transport"),
            tx(1, "50", "Income", month=10),
        ])

        self.assertEqual([s.month for s in summaries], ["2026-09", "2026-10"])

        september = summaries[0]
        self.assertEqual(september.money_in, Decimal("1000"))
        self.assertEqual(september.money_out, Decimal("600"))
        self.assertEqual(september.left_over, Decimal("400"))
        self.assertEqual(september.spending, [("Food", Decimal("500")), ("Transport", Decimal("100"))])

    def test_month_with_only_income(self):
        (summary,) = summarise([tx(1, "500", "Income")])
        self.assertEqual(summary.money_out, Decimal("0"))
        self.assertEqual(summary.spending, [])
        self.assertIn("Money in", render_month(summary))


class FormatMoneyTests(unittest.TestCase):
    def test_thousands_and_decimals(self):
        self.assertEqual(format_money(Decimal("1234567.5")), "₦1,234,567.50")

    def test_negative(self):
        self.assertEqual(format_money(Decimal("-20"), "$"), "-$20.00")


if __name__ == "__main__":
    unittest.main()
