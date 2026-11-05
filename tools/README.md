# SMS → data sheet

`sms_to_sheet.py` turns your phone's SMS export into masked rows for the **SMS samples** tab of the *CashFlowLens_Data_Collection* sheet. Python 3.8+ only; nothing to install.

## 1. Export your SMS (Android)

Install **SMS Backup & Restore** (SyncTech) → **Back up** → *Messages* only → save the `.xml` file and copy it to your computer.
A `.txt` (one message per line, or blank line between messages, optionally `SENDER: message`) or a `.csv` with a `body` column also works.

## 2. Run

```bash
python3 tools/sms_to_sheet.py sms-backup.xml --name "Your name" -o sms_rows.csv --preview 10
```

| Option | Meaning |
|---|---|
| `--name` | Goes in *Collected by* (required) |
| `--consent No` | Use when the messages aren't yours and the owner hasn't agreed (default `Yes`) |
| `--per-bank-type N` | Max rows per bank and transaction type, so the set stays varied (default 10; `0` = no limit) |
| `--keep-unknown` | Also keep alerts from sender IDs it doesn't recognise (never from personal phone numbers) |
| `--date YYYY-MM-DD` | *Date collected* (default today) |

What it does:
- **Keeps** only received bank, card, exchange-house and wallet transaction alerts.
- **Drops** OTP and code messages, promotions, balance-only alerts, personal chats and repeats of the same format.
- **Masks** account, card, reference and phone numbers (`XXXX`), names (`[NAME]`), UPI IDs (`[NAME]@okaxis`), links and e-mails, and balances (`AED X,XXX.XX`).
- **Keeps** the transaction amount, currency, dates, times, merchant and the bank's wording.
- **Fills** country, sender, bank (exact *Coverage* names), type, amount, currency, direction, merchant and an edge-case note, using only values the sheet's drop-downs accept.

The original text is never written to disk.

## 3. Check, then import

1. Open `sms_rows.csv` and **read every row**. Fix anything still personal or wrongly classified. The script is a first pass, not a guarantee.
2. In the sheet, click **B4** on *SMS samples* (or the first empty row in column B).
3. **File → Import → Upload** `sms_rows.csv` → **Replace data at selected cell**.
4. Column A fills in its own sample IDs; *Coverage* and *Start here* update by themselves.
5. Delete `sms_rows.csv` and the backup file when done.

## Tests

```bash
python3 -m unittest tools/test_sms_to_sheet.py
```
