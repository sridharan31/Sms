# SMS Finance: Investments and Expenses in USD / AED / INR

Reads your bank, card and broker SMS alerts. Sorts each message into **expense**,
**investment**, **income** or **redemption**, then shows the totals in **USD, AED and
INR** together. Works with UAE banks, Indian banks and brokers / fund platforms
(Zerodha, Groww, SIPs, IBKR, Sarwa, etc.). You only need Python 3.8+ and nothing
else to install.

## 1. Export your SMS

- **Android:** install *SMS Backup & Restore*, back up your messages to an `.xml`
  file and copy that file here.
- **Any phone:** copy the messages into a `.txt` file, one message per line or with a
  blank line between messages. A `.csv` file with a `body`/`message` column (and
  optionally `date` and `sender`) also works.

## 2. Run

```bash
python3 -m sms_finance sms-backup.xml --usd-inr 88.4 --monthly --csv transactions.csv
```

| Option | Meaning |
|---|---|
| `--usd-inr X` | INR per 1 USD. Set today's rate here (default 88.0) |
| `--aed-inr X` | Or give INR per 1 AED instead |
| `--usd-aed X` | AED per 1 USD (default 3.6725, the official peg) |
| `--from / --to YYYY-MM-DD` | Only count messages in this date range |
| `--monthly` | Month-by-month expense and investment table |
| `--csv FILE` | Save every detected transaction with USD/AED/INR columns |
| `--show-skipped` | List messages that were not recognised |

Try it on the sample messages:

```bash
python3 -m sms_finance examples/sample_sms.txt --monthly
```

## What you get

- Totals for income, expenses, investments and redemptions, plus **net cash flow**, in all three currencies
- The **share of outgoing money that went into investments**
- Investments split by type: Mutual funds / SIP, Stocks / brokerage, FD / RD, NPS / PPF, Gold
- Expenses split by category: Food, Groceries, Transport, Bills, Shopping, Rent, Travel, ...
- Totals in the currency each payment was actually made in

OTPs, promotional messages and balance-only alerts are ignored. If the transaction
amount and the balance appear in the same message, only the transaction amount is
counted.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```
