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


class RealWorldFormats(unittest.TestCase):
    """Formats seen in real exports (text invented)."""

    def test_free_text_and_people_masked(self):
        cases = [
            "INR 12,000.00 deposited to A/c No XX1234 towards 12345678901234 -TPT-Ti ravi Val 08-DEC-16.",
            "INR 20,000.00 deposited to A/c No XX1234 towards anil.k@okicici-123456789012-Kumar Val 06-DEC-17.",
            "INR 10,000.00 debited from A/c XX1234 on 02-JUL-18. Info: anil@okhdfcbank-PAY-123456789012-Rent for room. Avl bal:INR 1,000.00",
            "Rs. 5000.00 has been paid to ravikumar by 9876543210. Wallet txn id is 12345678901.",
            "Anil Kumar has sent Rs 5000 to your wallet. Upgrade your wallet.",
            "Salary of INR 24,850.00 credited to A/c XX1234 towards SALARY ACME SOFTWARE PVT LTD Value 30-NOV-2016.",
            "Paid Rs.50.00 to Acme Canteen Services at 1:38 PM. Wallet txn ID:12345678901",
        ]
        for body in cases:
            masked = s.mask_text(body)
            for secret in ("ravi", "anil", "Kumar", "Rent for room", "ACME", "Acme", "Anil"):
                self.assertNotIn(secret, masked, masked)

    def test_atm_place_masked(self):
        r, _ = row("JD-HDFCBK", "Rs.2000.00 was withdrawn using your HDFC Bank Card ending 1234 on 2016-12-01:07:22:45 at +PALAVAKKAM. Avl bal: Rs.100.00")
        self.assertNotIn("PALAVAKKAM", r["Masked message text (copy exactly, then mask)"])
        self.assertIn("at [PLACE]", r["Masked message text (copy exactly, then mask)"])

    def test_cashback_type(self):
        self.assertEqual(s.classify("You've received Rs. 300 cashback from Flipkart into your PhonePe wallet.", "x")[0], "Cashback / reward")

    def test_outstanding_masked(self):
        self.assertNotIn("9588", s.mask_text("Rs.427.00 was spent on ur Card ending 1234 at MOTI MAHAL. curr o/s - Rs.9588.00"))

    def test_loan_advert_dropped(self):
        r, d = row("BZHDFCBK", "Get Insta Loan upto Rs.41250 Credited in 1 Second to savings a/c. Eligibility valid till 25-Mar. TC Apply.")
        self.assertIsNone(r)

    def test_wallet_and_transfer_types(self):
        self.assertEqual(s.classify("Added Rs. 500 to your Paytm wallet. Get upto Rs 200 Cashback on Recharge", "x")[0], "Wallet top-up")
        self.assertEqual(s.classify("Request received to send Rs. 5000.00 to ANIL BANK 123. Updated Wallet Balance", "x"), ("Debit", "Out"))
        self.assertEqual(s.classify("Anil has sent Rs 5000 to your wallet.", "x"), ("Credit", "In"))
        self.assertEqual(s.classify("Your A/C XX123 debited for Rs 50.00 Towards POS withdrawal", "x")[0], "Card purchase")
        self.assertEqual(s.classify("NEFT txn for INR 8,000.00 has been credited to the beneficiary account", "HDFC Bank"), ("Debit", "Out"))


class MultiLine(unittest.TestCase):
    def test_card_alert_lines(self):
        body = ("Credit Card Purchase\nCard No XXXX2222\nAED 345.00\nSKYWAYS TRAVEL DUBAI ARE\n01/01/26 10:00\n"
                "Avl Bal AED 9876.00\nPay school fees in 12 instalments at 0% interest with no fees. Conditions apply.")
        rows, _ = s.process([("", body, "")], "T", "Yes", "SMS", "2026-11-05", 0, True)
        r = dict(zip(s.COLUMNS, rows[0]))
        self.assertEqual((r["Txn type"], r["Amount (as written)"], r["Currency"]), ("Card purchase", "345.00", "AED"))
        self.assertEqual(r["Merchant / counterparty"], "Skyways Travel")
        self.assertIn("\nAED 345.00\n", r["Masked message text (copy exactly, then mask)"])
        self.assertNotIn("2222", r["Masked message text (copy exactly, then mask)"])
        self.assertNotIn("9876", r["Masked message text (copy exactly, then mask)"])

    def test_idfc_formats(self):
        r, _ = row("", "Monthly interest of INR.12.00 earned on your Savings A/c XX1111 has been credited. New bal: INR.5000.00. IDFC FIRST Bank")
        self.assertEqual((r["Bank or provider"], r["Txn type"], r["Amount (as written)"]), ("IDFC FIRST Bank", "Interest", "12.00"))
        r, _ = row("", "Your A/c XX1111 debited by Rs. 1,000.00 on 01/01/26; Mr RAJA K credited. RRN 123456789012. Team IDFC FIRST Bank")
        self.assertNotIn("RAJA", r["Masked message text (copy exactly, then mask)"])


class Senders(unittest.TestCase):
    def test_sender_formats(self):
        for sender in ("JD-HDFCBK", "JD-HDFCBK-S", "MDHdfcBk", "IMHDFCBK", "HDFCBK"):
            self.assertEqual(s.identify_provider(sender, "")[0], "HDFC Bank", sender)
        self.assertEqual(s.identify_provider("VKiPaytm", "")[0], s.UPI_APPS)
        self.assertEqual(s.identify_provider("DMCANBNK", "")[0], "Canara Bank")
        self.assertIsNone(s.identify_provider("AXHATHWY", "Bill of Rs 500 paid"))


class Dedupe(unittest.TestCase):
    def test_same_format_kept_once(self):
        msgs = [("ENBD", f"Purchase of AED {n}.00 with Card ending 4321 at CARREFOUR on 03-11-2026", "") for n in (10, 20, 30)]
        rows, dropped = s.process(msgs, "T", "Yes", "SMS", "2026-11-05", 0, False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(dropped["Same format as one already kept"], 2)


if __name__ == "__main__":
    unittest.main()
