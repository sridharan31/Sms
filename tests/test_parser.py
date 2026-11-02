import unittest
from pathlib import Path

from sms_finance.loaders import load
from sms_finance.parser import extract_amount, parse_message
from sms_finance.rates import Converter
from sms_finance.report import summarize

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample_sms.txt"


class AmountTests(unittest.TestCase):
    def test_indian_grouping(self):
        self.assertEqual(extract_amount("Rs. 1,12,450.00 debited"), (112450.0, "INR"))

    def test_skips_balance(self):
        body = "Avl Bal AED 9,000.00. AED 50.00 spent at CAFE"
        self.assertEqual(extract_amount(body), (50.0, "AED"))

    def test_suffix_currency(self):
        self.assertEqual(extract_amount("Paid 300.50 AED to DEWA"), (300.5, "AED"))

    def test_symbols(self):
        self.assertEqual(extract_amount("charged $15.99 at NETFLIX"), (15.99, "USD"))
        self.assertEqual(extract_amount("₹650 debited via UPI"), (650.0, "INR"))


class ClassifyTests(unittest.TestCase):
    def test_sip_is_investment(self):
        t = parse_message("Rs. 5,000 debited towards SIP - Axis Mutual Fund")
        self.assertEqual((t.kind, t.category), ("investment", "Mutual funds / SIP"))

    def test_expense_category(self):
        t = parse_message("AED 62.00 spent on your card at TALABAT")
        self.assertEqual((t.kind, t.category), ("expense", "Food"))

    def test_salary(self):
        t = parse_message("Salary of AED 18,500.00 credited to your account")
        self.assertEqual((t.kind, t.category), ("income", "Salary"))

    def test_otp_ignored(self):
        self.assertIsNone(parse_message("Your OTP for transaction of AED 999.00 is 123456"))


class ConversionTests(unittest.TestCase):
    def test_aed_peg(self):
        c = Converter({"INR": 88.0})
        self.assertAlmostEqual(c.convert(3.6725, "AED", "USD"), 1.0)
        self.assertAlmostEqual(c.convert(1, "USD", "INR"), 88.0)
        self.assertAlmostEqual(c.convert(3.6725, "AED", "INR"), 88.0)


class SampleFileTests(unittest.TestCase):
    def test_sample_totals(self):
        txns = [t for b, d, s in load(SAMPLE) if (t := parse_message(b, d, s))]
        self.assertEqual(len(txns), 14)
        s = summarize(txns, Converter({"INR": 88.0}))
        self.assertEqual(s["counts"]["investment"], 4)
        self.assertEqual(s["counts"]["expense"], 7)
        src = s["by_source_currency"]["investment"]
        self.assertEqual(src, {"AED": 3000.0, "INR": 35000.0, "USD": 500.0})


if __name__ == "__main__":
    unittest.main()
