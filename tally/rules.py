"""Assigns a category to each transaction using keyword rules.

Rules live in a JSON file that maps a category to a list of keywords:

    {"Transport": ["bolt", "uber", "brt"], ...}

Keywords match whole words, case insensitive, so "data" matches
"MTN DATA BUNDLE" but not "UPDATE". Categories are checked in the order they
appear in the file and the first match wins, which lets you put specific rules
above general ones.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .models import Transaction

INCOME = "Income"
UNCATEGORISED = "Uncategorised"


@dataclass(frozen=True)
class Rule:
    category: str
    pattern: re.Pattern

    def matches(self, description: str) -> bool:
        return self.pattern.search(description) is not None


def build_rules(mapping: dict[str, list[str]]) -> list[Rule]:
    rules = []
    for category, keywords in mapping.items():
        if not keywords:
            continue
        alternatives = "|".join(re.escape(k.strip()) for k in keywords if k.strip())
        pattern = re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)
        rules.append(Rule(category, pattern))
    return rules


def load_rules(path: Path) -> list[Rule]:
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"rules file {path} does not exist") from None
    except json.JSONDecodeError as error:
        raise ValueError(f"rules file {path} is not valid JSON: {error}") from None

    if not isinstance(mapping, dict) or not all(isinstance(v, list) for v in mapping.values()):
        raise ValueError('rules file must look like {"Category": ["keyword", ...]}')

    return build_rules(mapping)


def categorise(transaction: Transaction, rules: list[Rule]) -> Transaction:
    if transaction.is_income:
        return transaction.with_category(INCOME)

    for rule in rules:
        if rule.matches(transaction.description):
            return transaction.with_category(rule.category)

    return transaction.with_category(UNCATEGORISED)


def categorise_all(transactions: list[Transaction], rules: list[Rule]) -> list[Transaction]:
    return [categorise(t, rules) for t in transactions]
