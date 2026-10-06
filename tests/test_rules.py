import unittest
from datetime import date
from decimal import Decimal

from tally.models import Transaction
from tally.rules import INCOME, UNCATEGORISED, build_rules, categorise


def spend(description: str, amount: str = "-1000") -> Transaction:
    return Transaction(day=date(2026, 9, 1), description=description, amount=Decimal(amount))


class CategoriseTests(unittest.TestCase):
    def setUp(self):
        self.rules = build_rules({
            "Rent": ["rent"],
            "Data & airtime": ["data", "airtime", "mtn"],
            "Transfers out": ["trf to"],
        })

    def test_keyword_match_is_case_insensitive(self):
        self.assertEqual(categorise(spend("MTN Data Bundle"), self.rules).category, "Data & airtime")

    def test_keywords_match_whole_words_only(self):
        # "data" must not match inside "update"
        self.assertEqual(categorise(spend("APP UPDATE FEE"), self.rules).category, UNCATEGORISED)

    def test_first_matching_category_wins(self):
        result = categorise(spend("NIP TRF TO LANDLORD RENT"), self.rules)
        self.assertEqual(result.category, "Rent")

    def test_money_in_is_always_income(self):
        result = categorise(spend("TRF TO ME REFUND", amount="5000"), self.rules)
        self.assertEqual(result.category, INCOME)

    def test_original_transaction_is_not_changed(self):
        original = spend("airtime")
        categorise(original, self.rules)
        self.assertIsNone(original.category)

    def test_keywords_with_special_characters(self):
        rules = build_rules({"Subscriptions": ["apple.com"]})
        self.assertEqual(categorise(spend("APPLE.COM/BILL"), rules).category, "Subscriptions")
        self.assertEqual(categorise(spend("APPLExCOM"), rules).category, UNCATEGORISED)


if __name__ == "__main__":
    unittest.main()
