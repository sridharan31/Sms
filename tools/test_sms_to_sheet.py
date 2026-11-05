"""Tests for sms_to_sheet.py. Messages are made up; run: python3 -m unittest tools/test_sms_to_sheet.py"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sms_to_sheet as s  # noqa: E402


def row(sender, body):
    rows, dropped = s.process([(sender, body, "")], "T", "Yes", "SMS", "2026-11-05", 0, False)
    return (dict(zip(s.COLUMNS, rows[0])) if rows else None), dropped


class Masking(unittest.TestCase):
    def test_keeps_amount_masks_card_and_balance(self):
        r, _ = row("ENBD", "Purchase of AED 1,247.30 with Card ending 4321 at CARREFOUR on 03-11-2026 14:22. Avl Bal AED 8,412.55")
        self.assertIn("AED 1,247.30", r["Masked message text (copy exactly, then mask)"])
        self.assertIn("ending XXXX", r["Masked message text (copy exactly, then mask)"])
        self.assertIn("AED X,XXX.XX", r["Masked message text (copy exactly, then mask)"])
        self.assertIn("03-11-2026 14:22", r["Masked message text (copy exactly, then mask)"])

    def test_masks_names_upi_ids_refs_and_phones(self):
        body = ("Dear SURESH NAIR, Rs.8,450.00 debited from A/c XX5678 to VPA rahul.kumar@okaxis "
                "UPI/P2A/412345678901/PRIYA MENON/SBIN Ref 412345678901. Call +91 98765 43210")
        masked = s.mask_text(body)
        for secret in ("SURESH", "rahul", "PRIYA", "5678", "412345678901", "98765", "43210"):
            self.assertNotIn(secret, masked)
        self.assertIn("Rs.8,450.00", masked)
        self.assertIn("[NAME]@okaxis", masked)
        self.assertIn("/SBIN", masked)

    def test_currency_word_is_not_a_name(self):
        masked = s.mask_text("A/c X1234 credited by Rs 25,000.00 transfer from PRIYA MENON")
        self.assertIn("by Rs 25,000.00", masked)
        self.assertNotIn("PRIYA", masked)

    def test_helpline_kept(self):
        self.assertIn("18002586161", s.mask_text("Rs.10.00 debited. Not you? Call 18002586161"))

    def test_no_long_digit_runs_left(self):
        masked = s.mask_text("INR 12,450.00 debited from A/c 123456789012 for EMI of loan 778899001122 ref 99887766")
        self.assertIsNone(re.search(r"\d{5,}", masked.replace("12,450.00", "")))


class Filtering(unittest.TestCase):
    def test_otp_dropped(self):
        r, d = row("VM-ICICIB", "123456 is your OTP for transaction of INR 2,500.00 at AMAZON.")
        self.assertIsNone(r)
        self.assertEqual(d["OTP / code"], 1)

    def test_promotion_dropped(self):
        r, _ = row("AD-KOTAKB", "Get up to Rs 5 lakh pre-approved personal loan! Apply now")
        self.assertIsNone(r)

    def test_personal_phone_sender_dropped(self):
        r, _ = row("+971501234567", "Hi bro sent you AED 200 for dinner")
        self.assertIsNone(r)

    def test_txn_with_otp_warning_kept(self):
        r, _ = row("JD-HDFCBK", "Rs.500.00 debited from A/c XX5678. Never share your OTP with anyone.")
        self.assertIsNotNone(r)


class Classification(unittest.TestCase):
    def check(self, sender, body, txn_type, direction, bank=None):
        r, _ = row(sender, body)
        self.assertIsNotNone(r, body)
        self.assertEqual(r["Txn type"], txn_type, body)
        self.assertEqual(r["Direction"], direction, body)
        self.assertIn(r["Txn type"], s.TXN_TYPES)
        self.assertIn(r["Country"], s.COUNTRIES)
        if bank:
            self.assertEqual(r["Bank or provider"], bank)
        return r

    def test_types(self):
        self.check("ENBD", "Purchase of AED 50.00 with Card ending 1234 at TALABAT on 03-11-2026", "Card purchase", "Out", "Emirates NBD")
        self.check("ADCBAlert", "Your salary AED 18,000.00 has been credited to your account XXX9012", "Salary", "In", "ADCB")
        self.check("Mashreq", "Your transaction of AED 350.00 at NOON was declined", "Declined / failed", "None (info only)")
        self.check("FAB", "A pre-authorization of USD 150.00 was made on your card ending 7788 at HILTON", "Card hold", "None (info only)")
        self.check("AX-AXISBK", "INR 12,450.00 debited from A/c XX3456 for EMI of loan account 7788", "EMI / loan", "Out", "Axis Bank")
        self.check("ENBD", "Refund of AED 89.00 from TALABAT has been credited to your card", "Refund / reversal", "In")
        self.check("JD-HDFCBK", "Rs.500.00 withdrawn at ATM on 03-11-26 from A/c XX5678", "ATM withdrawal", "Out")
        self.check("AlAnsari", "AED 5,000.00 remitted to beneficiary JOSEPH THOMAS. Fee AED 15.00", "Remittance sent", "Out", "Al Ansari Exchange")
        self.check("LuLuMoney", "Your transfer of AED 2,000.00 to MOHAMMED ALI is successful. Amount credited INR 51,200.00", "Remittance sent", "Out", "LuLu Exchange")
        self.check("JD-HDFCBK-S", "Payment of Rs.15,000.00 received towards your HDFC Bank Credit Card XX1234", "Card bill payment", "In")

    def test_merchant_and_foreign_note(self):
        r = self.check("FAB", "USD 19.99 spent on card XX1234 at NETFLIX.COM on 01-11-2026", "Card purchase", "Out")
        self.assertEqual(r["Merchant / counterparty"], "Netflix")
        self.assertIn("Foreign-currency", r["Edge-case note"])


class Dedupe(unittest.TestCase):
    def test_same_format_kept_once(self):
        msgs = [("ENBD", f"Purchase of AED {n}.00 with Card ending 4321 at CARREFOUR on 03-11-2026", "") for n in (10, 20, 30)]
        rows, dropped = s.process(msgs, "T", "Yes", "SMS", "2026-11-05", 0, False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(dropped["Same format as one already kept"], 2)


if __name__ == "__main__":
    unittest.main()
