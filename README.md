# Tally

A command line tool that reads a bank statement exported as CSV, puts every transaction into a category, and prints a summary for each month.

Kobo, the budget app I built before, needs every expense typed in by hand. A bank statement already has all of that data, so Tally sorts it instead.

```
$ python -m tally samples/statement.csv --month 2026-09

September 2026
==============

  Money in        ₦338,990.00
  Money out       ₦251,505.00
  Left over        ₦87,485.00

  Spending by category

  Rent             ₦90,000.00   36%  █████████
  Food             ₦61,170.00   24%  ██████
  Transfers out    ₦40,000.00   16%  ████
  Bills            ₦22,600.00    9%  ██
  Shopping          ₦9,500.00    4%  █
  Uncategorised     ₦8,900.00    4%  █
  Data & airtime    ₦7,500.00    3%  █
  Transport         ₦5,900.00    2%  █
  Subscriptions     ₦5,700.00    2%  █
  Bank charges        ₦235.00    0%  █
```

The sample statement in `samples/` is made up, but it follows the column layout Nigerian banks use for their CSV exports.

## Requirements

Python 3.10 or newer. Only the standard library, nothing to install.

## Usage

```
python -m tally STATEMENT.csv                      summary for every month in the file
python -m tally STATEMENT.csv --month 2026-09      one month only
python -m tally STATEMENT.csv --uncategorised      what no rule matched yet
python -m tally STATEMENT.csv --category food      every transaction in one category
python -m tally STATEMENT.csv --export out.csv     save the categorised rows
python -m tally STATEMENT.csv --rules mine.json    use your own keywords
```

## Rules

Categories come from a JSON file of keywords. The default one is `tally/default_rules.json`:

```json
{
  "Rent": ["rent", "landlord"],
  "Transport": ["bolt", "uber", "indrive", "brt", "fuel"],
  "Data & airtime": ["airtime", "data", "mtn", "airtel", "glo"]
}
```

- Keywords match whole words and ignore case, so `data` matches "MTN DATA BUNDLE" but not "APP UPDATE"
- The first category that matches wins, so specific rules go above general ones. "NIP TRF TO LANDLORD RENT" is Rent, not Transfers out, because Rent comes first
- Money coming in is always Income

The usual way to use it: run `--uncategorised`, see what is left over, add keywords, run again.

## Reading different banks

Every bank names its columns differently, so `reader.py` looks for a list of known names for each column instead of one exact header. It handles:

- Separate Debit and Credit columns, or one signed Amount column
- Dates like `2026-09-03`, `03/09/2026`, `03-Sep-2026`
- Amounts with commas, a naira sign, or brackets for negatives
- Blank lines at the end of the file, and the invisible byte-order mark Excel adds to the start

If a row cannot be read, the error says which line of the file it is on.

## Structure

```
tally/
  models.py     the Transaction dataclass
  reader.py     CSV to transactions
  rules.py      keyword rules and categorising
  report.py     monthly totals and the text output
  cli.py        command line arguments
tests/          23 unit tests
```

Amounts use `Decimal` rather than `float` for the same reason Kobo stores kobo instead of naira: floats cannot represent most decimal amounts exactly.

## Tests

```
python -m unittest
```
