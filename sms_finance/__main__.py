import argparse
import sys

from .loaders import load
from .parser import parse_message
from .rates import Converter, DEFAULT_RATES
from .report import render_text, summarize, write_csv


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m sms_finance",
        description="Calculate investments and expenses from bank SMS in USD, AED and INR.",
    )
    p.add_argument("files", nargs="+", help="SMS export(s): .xml (SMS Backup & Restore), .csv or .txt")
    p.add_argument("--usd-inr", type=float, help=f"INR per 1 USD (default {DEFAULT_RATES['INR']})")
    p.add_argument("--usd-aed", type=float, help=f"AED per 1 USD (default {DEFAULT_RATES['AED']}, pegged)")
    p.add_argument("--aed-inr", type=float, help="INR per 1 AED (sets the INR rate via the AED peg)")
    p.add_argument("--from", dest="date_from", help="only include messages on/after YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", help="only include messages on/before YYYY-MM-DD")
    p.add_argument("--monthly", action="store_true", help="show a month-by-month breakdown")
    p.add_argument("--csv", help="write every detected transaction to this CSV file")
    p.add_argument("--show-skipped", action="store_true", help="list messages that were not recognised")
    args = p.parse_args(argv)

    rates = {"AED": args.usd_aed, "INR": args.usd_inr}
    if args.aed_inr:
        rates["INR"] = args.aed_inr * (args.usd_aed or DEFAULT_RATES["AED"])
    conv = Converter(rates)

    txns, skipped = [], []
    for path in args.files:
        for body, date, sender in load(path):
            t = parse_message(body, date=date, sender=sender)
            (txns if t else skipped).append(t or body)

    if args.date_from or args.date_to:
        lo = args.date_from or "0000-00-00"
        hi = args.date_to or "9999-99-99"
        txns = [t for t in txns if t.date and lo <= t.date.strftime("%Y-%m-%d") <= hi]

    if not txns:
        print("No transactions found in the given messages.", file=sys.stderr)
        return 1

    print(f"Read {len(txns) + len(skipped)} messages, {len(txns)} transactions detected.\n")
    print(render_text(summarize(txns, conv), conv, by_month=args.monthly))

    if args.csv:
        write_csv(txns, conv, args.csv)
        print(f"\nTransactions written to {args.csv}")
    if args.show_skipped and skipped:
        print("\n== Not recognised ==")
        for s in skipped:
            print(" -", s[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
