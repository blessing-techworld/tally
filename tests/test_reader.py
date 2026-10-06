import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from tally.reader import StatementError, parse_amount, parse_date, read_statement


class ParseAmountTests(unittest.TestCase):
    def test_commas_and_currency_are_ignored(self):
        self.assertEqual(parse_amount("₦1,250.50"), Decimal("1250.50"))

    def test_empty_cell_is_zero(self):
        self.assertEqual(parse_amount(""), Decimal("0"))
        self.assertEqual(parse_amount(None), Decimal("0"))

    def test_brackets_mean_negative(self):
        self.assertEqual(parse_amount("(500.00)"), Decimal("-500.00"))

    def test_rubbish_raises(self):
        with self.assertRaises(ValueError):
            parse_amount("twelve")


class ParseDateTests(unittest.TestCase):
    def test_common_bank_formats(self):
        expected = date(2026, 9, 3)
        for text in ("2026-09-03", "03/09/2026", "03-Sep-2026", "03 Sep 2026"):
            with self.subTest(text=text):
                self.assertEqual(parse_date(text), expected)

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            parse_date("September third")


class ReadStatementTests(unittest.TestCase):
    def csv(self, text: str) -> Path:
        file = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
        file.write(text)
        file.close()
        path = Path(file.name)
        self.addCleanup(path.unlink)
        return path

    def test_debit_and_credit_columns(self):
        path = self.csv(
            "Trans. Date,Narration,Debit,Credit,Balance\n"
            "01-Sep-2026,SALARY,,\"100,000.00\",\"100,000.00\"\n"
            "02-Sep-2026,BOLT TRIP,\"2,500.00\",,\"97,500.00\"\n"
        )
        rows = read_statement(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].amount, Decimal("100000.00"))
        self.assertEqual(rows[1].amount, Decimal("-2500.00"))
        self.assertEqual(rows[1].description, "BOLT TRIP")

    def test_single_signed_amount_column(self):
        path = self.csv("Date,Description,Amount\n2026-09-01,Shoprite,-4500\n2026-09-02,Refund,1200\n")
        amounts = [t.amount for t in read_statement(path)]
        self.assertEqual(amounts, [Decimal("-4500"), Decimal("1200")])

    def test_headers_are_matched_without_case_or_spaces(self):
        path = self.csv(" DATE , DETAILS ,AMOUNT\n2026-09-01,x,-1\n")
        self.assertEqual(len(read_statement(path)), 1)

    def test_blank_lines_and_zero_rows_are_skipped(self):
        path = self.csv("Date,Description,Amount\n2026-09-01,x,-1\n,,\n2026-09-02,y,0\n")
        self.assertEqual(len(read_statement(path)), 1)

    def test_bad_row_reports_line_number(self):
        path = self.csv("Date,Description,Amount\n2026-09-01,x,-1\nyesterday,y,-2\n")
        with self.assertRaisesRegex(StatementError, "line 3"):
            read_statement(path)

    def test_missing_columns(self):
        path = self.csv("Foo,Bar\n1,2\n")
        with self.assertRaisesRegex(StatementError, "date and a description"):
            read_statement(path)

    def test_missing_file(self):
        with self.assertRaises(StatementError):
            read_statement(Path("does-not-exist.csv"))


if __name__ == "__main__":
    unittest.main()
