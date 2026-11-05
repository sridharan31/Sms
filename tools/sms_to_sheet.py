#!/usr/bin/env python3
"""Turn a phone's SMS export into masked rows for the CashFlowLens data sheet.

Reads an SMS export, keeps only bank / card / exchange-house / wallet
transaction alerts, masks personal data, works out the fields, and writes a CSV
whose columns match the "SMS samples" tab from column B to column Q.

Supported inputs:
  * SMS Backup & Restore XML (Android app "SMS Backup & Restore")
  * CSV with a body/message/text column (and optional sender/address, date)
  * Plain text: one message per line, or messages separated by blank lines.
    A line may start with the sender, e.g. "JD-HDFCBK: Rs.500 debited ..."

The original message text is never written anywhere; only masked text is.

Usage:
  python3 sms_to_sheet.py sms-backup.xml --name "Your name" -o sms_rows.csv
  python3 sms_to_sheet.py messages.txt --name "Your name" --preview 10

Then in Google Sheets: click cell B4 of "SMS samples" (or the first empty row
in column B), File > Import > Upload sms_rows.csv > "Replace data at selected
cell". Column A fills in its own sample IDs. Read every row before relying on it.

Standard library only; Python 3.8+.
"""

import argparse
import csv
import datetime as dt
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Sheet vocabulary (must match the "Lists" tab so the drop-downs accept it)
# ---------------------------------------------------------------------------

COUNTRIES = {"UAE", "India", "Other"}
CURRENCIES = {"AED", "INR", "USD", "EUR", "GBP", "SAR"}  # anything else -> "Other"
TXN_TYPES = [
    "Card purchase", "Debit", "Credit", "Salary", "Refund / reversal",
    "Partial refund", "Card hold", "Declined / failed", "Cashback / reward",
    "Transfer own account", "Remittance sent", "Remittance received",
    "EMI / loan", "Card converted to EMI", "Autopay / mandate set-up",
    "ATM withdrawal", "Card bill payment", "Wallet top-up",
    "Bank fee / FX fee", "Interest", "Other",
]
OUT, IN, NONE = "Out", "In", "None (info only)"

COLUMNS = [  # columns B..Q of "SMS samples"
    "Date collected", "Country", "Source", "Sender ID / app", "Bank or provider",
    "Masked message text (copy exactly, then mask)", "Txn type",
    "Amount (as written)", "Currency", "Direction", "Merchant / counterparty",
    "Edge-case note", "Personal data masked?", "Owner consent?", "Collected by",
    "Notes",
]

# ---------------------------------------------------------------------------
# Banks and providers. Names match the "Coverage" tab exactly.
# Keys are sender IDs with the operator prefix/suffix removed, upper case,
# letters and digits only. A key also matches senders that start with it.
# ---------------------------------------------------------------------------

UPI_APPS = "UPI apps (GPay, PhonePe, Paytm)"
PROVIDERS = {
    # UAE
    "ENBD": ("Emirates NBD", "UAE"), "EMIRATESNBD": ("Emirates NBD", "UAE"),
    "FAB": ("First Abu Dhabi Bank (FAB)", "UAE"), "FABBANK": ("First Abu Dhabi Bank (FAB)", "UAE"),
    "ADCB": ("ADCB", "UAE"),
    "MASHREQ": ("Mashreq", "UAE"),
    "DIB": ("Dubai Islamic Bank", "UAE"),
    "ADIB": ("ADIB", "UAE"),
    "RAKBANK": ("RAKBANK", "UAE"),
    "CBD": ("Commercial Bank of Dubai", "UAE"),
    "ALANSARI": ("Al Ansari Exchange", "UAE"), "ANSARI": ("Al Ansari Exchange", "UAE"),
    "LULU": ("LuLu Exchange", "UAE"),
    "WISE": ("Wise", "UAE"),
    # India
    "SBIINB": ("State Bank of India", "India"), "SBIUPI": ("State Bank of India", "India"),
    "SBIPSG": ("State Bank of India", "India"), "CBSSBI": ("State Bank of India", "India"),
    "ATMSBI": ("State Bank of India", "India"), "SBIBNK": ("State Bank of India", "India"),
    "HDFCBK": ("HDFC Bank", "India"), "HDFCBN": ("HDFC Bank", "India"),
    "ICICIB": ("ICICI Bank", "India"), "ICICIT": ("ICICI Bank", "India"),
    "AXISBK": ("Axis Bank", "India"), "AXISMR": ("Axis Bank", "India"),
    "KOTAKB": ("Kotak Mahindra Bank", "India"), "KOTAK": ("Kotak Mahindra Bank", "India"),
    "FEDBNK": ("Federal Bank", "India"), "FEDBK": ("Federal Bank", "India"),
    "CANBNK": ("Canara Bank", "India"),
    "IDFCFB": ("IDFC FIRST Bank", "India"), "IDFCBK": ("IDFC FIRST Bank", "India"), "IDFC": ("IDFC FIRST Bank", "India"),
    "BOBTXN": ("Bank of Baroda", "India"), "BOBSMS": ("Bank of Baroda", "India"),
    "BOBCRD": ("Bank of Baroda", "India"),
    "GPAY": (UPI_APPS, "India"), "GOOGLEPAY": (UPI_APPS, "India"),
    "PHONPE": (UPI_APPS, "India"), "PHONEPE": (UPI_APPS, "India"),
    "PAYTM": (UPI_APPS, "India"), "PYTM": (UPI_APPS, "India"), "IPAYTM": (UPI_APPS, "India"),
}
# Bank names that may appear in the message body (for short-code or unusual senders)
BODY_NAMES = [
    (r"emirates\s*nbd", "ENBD"), (r"first abu dhabi|\bFAB\b", "FAB"), (r"\bADCB\b", "ADCB"),
    (r"mashreq", "MASHREQ"), (r"dubai islamic", "DIB"), (r"\bADIB\b", "ADIB"),
    (r"rak\s*bank", "RAKBANK"), (r"commercial bank of dubai|\bCBD\b", "CBD"),
    (r"al\s*ansari", "ALANSARI"), (r"lulu\s*(exchange|money)", "LULU"), (r"\bwise\b", "WISE"),
    (r"\bSBI\b|state bank of india", "SBIINB"), (r"\bHDFC\b", "HDFCBK"), (r"\bICICI\b", "ICICIB"),
    (r"\baxis bank\b", "AXISBK"), (r"\bkotak\b", "KOTAKB"), (r"federal bank", "FEDBNK"),
    (r"canara bank", "CANBNK"), (r"IDFC\s*FIRST", "IDFCFB"), (r"bank of baroda|\bBOB\b", "BOBTXN"),
]
EXCHANGE_HOUSES = {"Al Ansari Exchange", "LuLu Exchange", "Wise"}


def sender_core(sender):
    s = (sender or "").strip().upper()
    s = re.sub(r"^[A-Z]{2}-", "", s)          # Indian operator prefix, e.g. JD-
    s = re.sub(r"-[A-Z]$", "", s)             # TRAI suffix, e.g. -S, -T
    return re.sub(r"[^A-Z0-9]", "", s)


def is_phone_number(sender):
    return bool(re.fullmatch(r"\+?[\d\s-]{6,}", (sender or "").strip()))


def identify_provider(sender, body):
    core = sender_core(sender)
    # older Indian IDs have the 2-letter operator prefix without a hyphen, e.g. "MDHdfcBk"
    candidates = [core] + ([core[2:]] if len(core) >= 7 and core[:2].isalpha() else [])
    for c in candidates:
        for key in sorted(PROVIDERS, key=len, reverse=True):
            if c == key or c.startswith(key):
                return PROVIDERS[key]
    for pattern, key in BODY_NAMES:
        if re.search(pattern, body, re.I):
            return PROVIDERS[key]
    return None


# ---------------------------------------------------------------------------
# Amounts
# ---------------------------------------------------------------------------

_NUM = r"\d{1,3}(?:,\d{2,3})+(?:\.\d{1,3})?|\d+(?:\.\d{1,3})?"
_CUR = (r"AED|Dhs?\.?|DHS|INR|Rs\.?|₹|USD|US\$|\$|EUR|€|GBP|£|SAR|SR|QAR|OMR|KWD|BHD|"
        r"PHP|PKR|LKR|NPR|BDT|SGD|AUD|CAD")
AMOUNT_RE = re.compile(
    rf"(?P<c1>{_CUR})(?:(?<!\.)[.:])?[ \t]?(?P<n1>{_NUM})|(?P<n2>{_NUM})[ \t]?(?P<c2>AED|INR|USD|EUR|GBP|SAR|Dhs|DHS|Rs)\b",
    re.I,
)
CUR_MAP = {"aed": "AED", "dh": "AED", "dhs": "AED", "inr": "INR", "rs": "INR", "₹": "INR",
           "usd": "USD", "us$": "USD", "$": "USD", "eur": "EUR", "€": "EUR",
           "gbp": "GBP", "£": "GBP", "sar": "SAR", "sr": "SAR"}
BALANCE_CONTEXT = re.compile(
    r"(bal(ance)?|avl|avail(able)?|limit|outstanding|o/s|total\s+due|min(imum)?\s+(amount\s+)?due|"
    r"amount\s+due|amt\s+due|due\s+amount)[\s:.\-a-z]{0,20}$",
    re.I,
)


def find_amounts(text):
    """Return list of (start, end, amount_text, currency_code, is_balance)."""
    found = []
    for m in AMOUNT_RE.finditer(text):
        cur = (m.group("c1") or m.group("c2") or "").lower().rstrip(".")
        num = m.group("n1") or m.group("n2")
        code = CUR_MAP.get(cur, cur.upper())
        if code not in CURRENCIES:
            code = "Other"
        before = text[max(0, m.start() - 30):m.start()]
        found.append((m.start(), m.end(), num, code, bool(BALANCE_CONTEXT.search(before))))
    return found


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

OTP_RE = re.compile(
    r"(\b(otp|one[\s-]?time\s+(password|pin|code)|verification\s+code|security\s+code|passcode|"
    r"activation\s+code|code)\b[^.\n]{0,25}?\b(is|:)?\s*\d{4,8}\b)"
    r"|(\b\d{4,8}\b\s*(is|as)\s+(your|the)\s+(otp|one[\s-]?time|verification|security|code|pin))"
    r"|(\buse\s+\d{4,8}\b)",
    re.I,
)
PROMO_RE = re.compile(
    r"pre-?approved|apply\s+now|\boffer\b|get\s+up\s+to|click|limited\s+period|congratulations|"
    r"\bwin\b|eligible\s+for|T&C|download\s+(the\s+)?app|upgrade\s+now|avail\s+now|instant\s+loan",
    re.I,
)
# Adverts that mention "credited" etc. but are never real transactions
HARD_PROMO_RE = re.compile(r"eligib|T\s?&?\s?C\s+apply|insta(nt)?\s+(jumbo\s+)?loan|jumbo\s+loan|apply\s+now|"
                           r"pre-?approved|plan\s+your|shop\s+now\s*$", re.I)
DONE_VERB_RE = re.compile(
    r"debited|credited|spent|purchase|withdrawn|received|sent|transferred|paid|refund|revers|"
    r"declin|failed|deducted|charged|deposited|cashback|mandate|autopay|pre-?auth|hold|blocked|"
    r"converted|payment|remit|\bcr\b|\bdr\b|successful",
    re.I,
)
INFO_ONLY_RE = re.compile(r"\bmandate|auto-?pay|standing\s+instruction|e-?mandate", re.I)


# ---------------------------------------------------------------------------
# Masking
# ---------------------------------------------------------------------------

MONTHS = r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
PROTECT_RES = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?\b"),
    re.compile(r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b"),
    re.compile(rf"\b\d{{1,2}}[- ]?(?:{MONTHS})[a-z]*[- ,]*\d{{2,4}}\b", re.I),
    re.compile(rf"\b(?:{MONTHS})[a-z]*[- ]\d{{1,2}},?[- ]\d{{2,4}}\b", re.I),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?\b", re.I),
    re.compile(r"\b(?:1800|1860)[\d -]{3,10}\d\b"),      # Indian toll-free helplines
    re.compile(r"\b(?:600|800)\s?\d{2,3}\s?\d{3,4}\b"),  # UAE 600/800 helplines
]
NAME_STOP = {
    "a/c", "ac", "acct", "account", "card", "your", "ur", "you", "vpa", "upi", "neft", "imps",
    "rtgs", "atm", "the", "bank", "beneficiary", "ref", "credit", "debit", "salary", "wallet",
    "merchant", "cash", "india", "uae", "self", "own", "mobile", "a", "an", "xx", "xxxx", "on",
    "customer", "cardholder", "emi", "loan", "upi-id", "linked", "registered", "us", "other",
    "rs", "rs.", "inr", "aed", "dhs", "usd", "eur", "gbp", "sar", "cheque", "cash", "pos", "net",
    "internet", "branch", "salary", "employer",
}
# Lead words that always mean a person or account holder follows
PERSON_LEADS = re.compile(r"transferred to|transfer to|trf to|sent to|paid to|received from|credited by|beneficiary", re.I)
UPI_KEEP = {"P2A", "P2M", "CR", "DR", "UPI", "IMPS", "NEFT", "RTGS", "MMT", "PAY", "COLLECT", "REV"}


def _protected_spans(text, amounts):
    spans = [(s, e) for s, e, _, _, is_bal in amounts if not is_bal]
    for rx in PROTECT_RES:
        spans += [m.span() for m in rx.finditer(text)]
    return spans


def _inside(pos, spans):
    return any(s <= pos < e for s, e in spans)


def _mask_upi_chain(m):
    parts = m.group(0).split("/")
    out = [parts[0]]
    for p in parts[1:]:
        q = p.strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z .]{2,}", q) and q.upper() not in UPI_KEEP \
                and not re.fullmatch(r"[A-Z]{4}", q):          # 4 letters = bank code, keep
            out.append("[NAME]")
        else:
            out.append(p)
    return "/".join(out)


def _mask_name_after(m):
    name = m.group("name")
    words = name.split()
    if not words or words[0].lower().strip(".:,") in NAME_STOP or "[" in name or "@" in name:
        return m.group(0)
    lead = m.group("lead").strip()
    if len(words) == 1 and not PERSON_LEADS.search(lead) and not re.search(r"UPI|VPA|IMPS|NEFT", m.string, re.I):
        return m.group(0)       # single word after plain from/to/by: usually a merchant
    if any(w.lower().strip(".:,") in NAME_STOP for w in words):
        # keep the words up to the first stop word as the name
        keep = []
        for w in words:
            if w.lower().strip(".:,") in NAME_STOP:
                break
            keep.append(w)
        rest = name[len(" ".join(keep)):]
        return m.group("lead") + "[NAME]" + rest if keep else m.group(0)
    return m.group("lead") + "[NAME]"


def mask_text(text):
    """Mask personal data. Keeps transaction amounts, currencies, dates, times, wording."""
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r" *\n[ \n]*", "\n", t).strip()
    # links, e-mails, UPI IDs
    t = re.sub(r"\bhttps?://\S+|\bwww\.\S+|\b[\w-]+\.(?:com|in|ae|co|ly|me|io|net|org)/\S*", "[LINK]", t, flags=re.I)
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "[EMAIL]", t)
    t = re.sub(r"\b[\w.\-]+@([A-Za-z][\w]{1,15})\b", r"[NAME]@\1", t)
    # greetings and names after transfer words
    t = re.sub(r"\b(Dear|Hi|Hello)\s+(?!(Customer|Cardholder|Member|Sir|Madam|Valued|User|Client)\b)"
               r"[A-Za-z][A-Za-z.]*(\s+[A-Z][A-Za-z.]*){0,2}", r"\1 [NAME]", t)
    # titled people, e.g. "; Mr RAJA K credited"
    t = re.sub(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Shri|Smt)\.?\s+[A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*){0,3}", "[NAME]", t)
    # free-text remarks and employer names
    t = re.sub(r"(-TPT-).*?(?=\s+Val\b|$)", r"\1[NOTE]", t)
    t = re.sub(r"(@[A-Za-z]{2,15}(?:-[A-Z]+)?-\d+-)[^.]*?(?=\s+Val\b|\.\s|$)", r"\1[NOTE]", t)
    t = re.sub(r"(towards\s+SALARY\s+|salary\s+(?:from|by)\s+).*?(?=\s+Val(?:ue)?\b|\.\s|$)", r"\1[EMPLOYER]", t, flags=re.I)
    t = re.sub(r"^(?:[A-Z][a-z]+\s+){1,3}(?=has\s+sent\b)", "[NAME] ", t)
    t = re.sub(r"(\b(?:paid|sent)\s+(?:rs\.?|inr|aed)?\s?[\d,.]+\s+to\s+|has been paid to\s+|\bsent you\s+)"
               r"(?!(your|a/c|the|VPA|\[|XX|account)\b)[A-Za-z][\w .&'-]*?(?=\s+(?:at|on|by|via|bank|for)\b|[.,;]|$)",
               r"\1[NAME]", t, flags=re.I)
    t = re.sub(r"\b(?:UPI|IMPS|NEFT|RTGS|MMT)(?:/[A-Za-z0-9.&@\-]+(?: [A-Z][A-Z.&]+){0,3})+", _mask_upi_chain, t)
    t = re.sub(
        r"(?P<lead>\b(?:transferred to|transfer to|trf to|sent to|paid to|received from|credited by|"
        r"from|to|by|beneficiary:?)\s+)(?P<name>[A-Z][A-Za-z.']*(?:\s+[A-Z][A-Za-z.']*){0,3})",
        _mask_name_after, t)
    # balances and limits: keep the format, hide the digits
    amounts = find_amounts(t)
    chars = list(t)
    for s, e, _, _, is_bal in amounts:
        if is_bal:
            for i in range(s, e):
                if chars[i].isdigit():
                    chars[i] = "X"
    t = "".join(chars)
    # every other run of 3+ digits (accounts, cards, references, phones) -> X
    amounts = find_amounts(t)
    spans = _protected_spans(t, amounts)
    chars = list(t)
    for m in re.finditer(r"\d{3,}", t):
        if not _inside(m.start(), spans):
            for i in range(m.start(), m.end()):
                chars[i] = "X"
    # phone numbers written with spaces, e.g. +971 50 123 4567
    t = "".join(chars)
    t = re.sub(r"\+\d{1,3}[\s-]?\d{1,2}(?=[\s-]?X)", lambda m: re.sub(r"\d", "X", m.group(0)), t)
    # alphanumeric reference codes with digits, e.g. TXN8F7K2Q1
    t = re.sub(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8,}\b",
               lambda m: m.group(0) if _looks_like_word(m.group(0)) else "[REF]", t)
    return t


def _looks_like_word(token):
    return not re.search(r"\d", token)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

DEBIT_RE = re.compile(r"debited|\bdebit\b|spent|\bpaid\b|\bsent\b|transferred|withdrawn|deducted|"
                      r"charged|purchase|\bdr\b|payment of|used for", re.I)
CREDIT_RE = re.compile(r"credited|\bcredit(?!\s*card)\b|received|deposited|\bcr\b|added|refund|cashback", re.I)

RULES = [  # (type, pattern) checked in order
    ("Declined / failed", r"declin|\bfailed\b|unsuccessful|insufficient|not processed|could not be processed|rejected"),
    ("Card converted to EMI", r"(converted|conversion)[^.]{0,40}\bEMI\b|\bEMI\b[^.]{0,40}(converted|conversion|booked)"),
    ("Card hold", r"pre-?auth|preauthori[sz]|on hold|amount (is )?held|hold of|\bblocked\b"),
    ("Partial refund", r"partial(ly)? refund"),
    ("Refund / reversal", r"refund|revers|chargeback|credited back"),
    ("Wallet top-up", r"added\s+rs\.?\s?[\d,.]+\s+to\s+your\s+\w*\s*wallet|top[- ]?up|wallet (load|recharge)"),
    ("Cashback / reward", r"(received|credited|earned).{0,30}cash ?back|cash ?back[^.]{0,30}(credited|received)|reward points? (credited|earned)"),
    ("Salary", r"\bsalary\b|\bsal\b|payroll|\bWPS\b"),
    ("Card bill payment", r"payment.{0,40}(received|credited).{0,60}card|card (bill|payment)|"
                          r"thank you for (your )?payment|credit card payment|\bCC payment|towards your card"),
    ("Card purchase", r"\bPOS\b"),
    ("ATM withdrawal", r"\bATM\b|cash withdraw|withdrawn|withdrawal"),
    ("EMI / loan", r"\bEMI\b|\bloan\b|instal+ment|\bNACH\b"),
    ("Wallet top-up", r"top[- ]?up|added to (your )?wallet|wallet (load|recharge)"),
    ("Transfer own account", r"(own|self) (a/c|account)|self[- ]transfer|between your accounts"),
    ("Bank fee / FX fee", r"\b(annual fee|late (payment )?fee|fee|charges?|markup|penalty|GST on|VAT on)\b"),
    ("Interest", r"\binterest\b"),
    ("Card purchase", r"purchase|\bspent\b|\bPOS\b|used (at|for)|card[^.]{0,60}\bat\b|\bat\b[^.]{0,40}card|txn[^.]{0,30}\bat\b"),
]
REMIT_RE = re.compile(r"remit|inward|international transfer|telegraphic|\bTT\b|money transfer|"
                      r"western union|transfer to india", re.I)
OUTGOING_RE = re.compile(r"request received to send|credited to the beneficiary|successfully sent|has been paid to", re.I)
INCOMING_RE = re.compile(r"has sent (rs\.?|inr)?\s?[\d,.]+ to your", re.I)
INWARD_RE = re.compile(r"inward|received from abroad|foreign inward|remittance received", re.I)


def classify(body, provider_name):
    """Return (txn_type, direction)."""
    is_debit = bool(DEBIT_RE.search(body))
    is_credit = bool(CREDIT_RE.search(body))
    if OUTGOING_RE.search(body):
        is_debit, is_credit = True, False
    elif INCOMING_RE.search(body):
        is_debit, is_credit = False, True
    if INFO_ONLY_RE.search(body) and re.search(r"regist|creat|set ?up|activat|success|approved", body, re.I) \
            and not re.search(r"debited|deducted", body, re.I):
        return "Autopay / mandate set-up", NONE
    for txn_type, pattern in RULES:
        if re.search(pattern, body, re.I):
            break
    else:
        txn_type = None
    if txn_type in (None, "Debit", "Credit", "Card purchase", "Bank fee / FX fee") and (
            provider_name in EXCHANGE_HOUSES or REMIT_RE.search(body)):
        outward = re.search(r"remitted|transfer(red)?\s+(of|to)|\bsent\b|debited|\bpaid\b", body, re.I)
        txn_type = "Remittance received" if (INWARD_RE.search(body) or (is_credit and not outward)) else "Remittance sent"
    if txn_type is None:
        txn_type = "Debit" if is_debit else "Credit" if is_credit else "Other"

    fixed = {
        "Declined / failed": NONE, "Card hold": NONE, "Card converted to EMI": NONE,
        "Card purchase": OUT, "ATM withdrawal": OUT, "EMI / loan": OUT, "Wallet top-up": OUT,
        "Bank fee / FX fee": OUT, "Remittance sent": OUT, "Debit": OUT,
        "Refund / reversal": IN, "Partial refund": IN, "Cashback / reward": IN, "Salary": IN,
        "Remittance received": IN, "Credit": IN,
    }
    if txn_type in fixed:
        return txn_type, fixed[txn_type]
    # direction depends on wording
    if is_debit and not is_credit:
        return txn_type, OUT
    if is_credit and not is_debit:
        return txn_type, IN
    if txn_type == "Card bill payment":
        return txn_type, IN if re.search(r"received|credited|thank you", body, re.I) else OUT
    return txn_type, NONE


TRAILING_PLACE = re.compile(
    r"\s+(DUBAI|ABU DHABI|SHARJAH|AJMAN|AL AIN|AE|ARE|UAE|IN|IND|INDIA|MUMBAI|DELHI|BANGALORE|BENGALURU|"
    r"CHENNAI|KOCHI|HYDERABAD|PUNE|KOLKATA|US|USA|GB|GBR|ABUDHABI|ABU DHABI|AUH|DXB)$", re.I)
PROMO_LINE_RE = re.compile(r"[^.\n]*(conditions apply|0% interest|instal+ments at|T&C|offer)[^.\n]*\.?", re.I)


def merchant_of(masked, txn_type):
    if txn_type == "Salary":
        return "Salary"
    if txn_type == "ATM withdrawal":
        return "ATM"
    m = re.search(r"\b(?:at|@)\s+(?P<m>[A-Za-z0-9*&.'\- ]{2,40}?)(?=\s+(?:on|dated|via|using|for|txn|with|ref|in|"
                  r"Avl|Avail|Bal|\d)\b|[.,;]|$)", masked)
    if not m:
        m = re.search(r";\s*(?P<m>[^;\[\]]{2,40}?)\s+credited\b", masked)
    if not m:
        m = re.search(r"Bill Payment of .{0,20}? for (?P<m>[A-Za-z][A-Za-z .&\-]{2,40}?)(?=\s+-|\s+for\b|[.,]|$)", masked)
    if not m and "\n" in masked:
        lines = masked.split("\n")
        for i, line in enumerate(lines[:-1]):
            if AMOUNT_RE.fullmatch(line.strip()) and re.search(r"[A-Za-z]{3}", lines[i + 1]) \
                    and not AMOUNT_RE.search(lines[i + 1]):
                m = re.match(r"(?P<m>.+)", lines[i + 1].strip())
                break
    if not m and txn_type in ("Refund / reversal", "Partial refund", "Cashback / reward"):
        m = re.search(r"\bfrom\s+(?P<m>[A-Za-z0-9*&.'\- ]{2,40}?)(?=\s+(?:has|have|is|was|on|for|to|of|ref|into|in)\b|[.,;]|$)", masked)
    if m and not m.group("m").strip().startswith("["):
        name = re.sub(r"\s+", " ", m.group("m")).strip(" .-*")
        for _ in range(2):
            name = TRAILING_PLACE.sub("", name)
        return name.title() if name.isupper() else name
    if "[NAME]" in masked:
        return "[NAME] (UPI)" if re.search(r"UPI|VPA|@", masked, re.I) else "[NAME]"
    return ""


EDGE_NOTES = {
    "Card hold": "Hold: not the final amount",
    "Declined / failed": "Declined: must not be counted",
    "Refund / reversal": "Refund: links to the original purchase",
    "Partial refund": "Partial refund: reduces the original",
    "Autopay / mandate set-up": "Mandate set-up: not a transaction",
    "Card converted to EMI": "Purchase converted to EMI",
    "ATM withdrawal": "Cash: transfer to cash wallet",
    "Card bill payment": "Card bill: transfer between own accounts",
    "Transfer own account": "Own-account transfer",
    "Wallet top-up": "Wallet top-up: transfer",
    "Remittance sent": "Remittance: check fee and rate",
}


def edge_note(masked, txn_type, country, currency):
    notes = []
    if txn_type in EDGE_NOTES:
        notes.append(EDGE_NOTES[txn_type])
    home = {"UAE": "AED", "India": "INR"}.get(country)
    if home and currency not in (home, "Other") and txn_type not in ("Remittance sent", "Remittance received"):
        notes.append("Foreign-currency transaction")
    if re.search(r"markup|\bDCC\b|foreign (currency|transaction)|cross[- ]?currency", masked, re.I):
        notes.append("FX fee or markup mentioned")
    if txn_type in ("Debit", "Credit") and "[NAME]" in masked and re.search(r"UPI|VPA|@", masked, re.I):
        notes.append("UPI transfer to/from a person")
    return "; ".join(notes)


# ---------------------------------------------------------------------------
# Reading exports
# ---------------------------------------------------------------------------

def read_xml(path):
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "sms":
            if el.get("type", "1") == "1":                       # received messages only
                yield el.get("address", ""), el.get("body", ""), el.get("date", "")
            el.clear()


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = {k.lower().strip(): k for k in (reader.fieldnames or [])}
        body_k = next((fields[k] for k in ("body", "message", "text", "sms", "content") if k in fields), None)
        if body_k is None:
            raise SystemExit("CSV needs a column named body, message or text.")
        snd_k = next((fields[k] for k in ("sender", "address", "from", "sender id") if k in fields), None)
        date_k = next((fields[k] for k in ("date", "time", "timestamp") if k in fields), None)
        for row in reader:
            yield (row.get(snd_k, "") if snd_k else ""), row.get(body_k, ""), (row.get(date_k, "") if date_k else "")


SENDER_PREFIX = re.compile(r"^\s*(?P<s>[A-Z]{2}-[A-Z0-9]{3,9}(?:-[A-Z])?|[A-Za-z][A-Za-z0-9]{2,15})\s*[:|>]\s+(?P<b>.+)$", re.S)


def read_txt(path):
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    chunks = re.split(r"\n\s*\n", raw) if re.search(r"\n\s*\n", raw) else raw.splitlines()
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = SENDER_PREFIX.match(chunk)
        yield (m.group("s"), m.group("b"), "") if m else ("", chunk, "")


def read_messages(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".xml":
        return read_xml(path)
    if suffix == ".csv":
        return read_csv(path)
    return read_txt(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process(messages, name, consent, source, today, per_bank_type, keep_unknown):
    rows, seen, per_key, dropped = [], set(), Counter(), Counter()
    for sender, body, _date in messages:
        body = (body or "").strip()
        if not body:
            continue
        if OTP_RE.search(body):
            dropped["OTP / code"] += 1
            continue
        if HARD_PROMO_RE.search(body) and not re.search(r"\b(added|paid|sent|withdrawn|spent)\b", body, re.I):
            dropped["Promotion"] += 1
            continue
        if PROMO_RE.search(body) and not re.search(r"debited|credited|spent|withdrawn|refund|revers|declin", body, re.I):
            dropped["Promotion"] += 1
            continue
        provider = identify_provider(sender, body)
        if provider is None and (is_phone_number(sender) or not keep_unknown):
            dropped["Not from a known bank or provider"] += 1
            continue
        amounts = find_amounts(body)
        txn_amounts = [a for a in amounts if not a[4]]
        if not txn_amounts and not INFO_ONLY_RE.search(body):
            dropped["No transaction amount (balance or info only)"] += 1
            continue
        if not DONE_VERB_RE.search(body):
            dropped["No transaction wording"] += 1
            continue

        bank, country = provider if provider else ("", "")
        txn_type, direction = classify(PROMO_LINE_RE.sub("", body), bank)
        amount, currency = (txn_amounts[0][2], txn_amounts[0][3]) if txn_amounts else ("", "")
        if not country:
            country = {"AED": "UAE", "INR": "India"}.get(currency, "Other")
        masked = mask_text(body)
        if txn_type == "ATM withdrawal":      # ATM and branch locations can show where someone lives
            masked = re.sub(r"(\bat\s+)\+?[A-Za-z0-9 .\-/&]+?(?=\.\s|\.?\s*Avl|\s+on\b|$)", r"\1[PLACE]", masked)
        masked = re.sub(r"(CASH\s+DEP(?:OSIT)?\s+)[A-Za-z .\-]+?(?=\s+Val\b|[.,]|$)", r"\1[PLACE]", masked, flags=re.I)

        shape = re.sub(r"[\dX]+", "9", masked)
        if shape in seen:
            dropped["Same format as one already kept"] += 1
            continue
        key = (bank, txn_type)
        if per_bank_type and per_key[key] >= per_bank_type:
            dropped["Enough of this bank and type"] += 1
            continue
        seen.add(shape)
        per_key[key] += 1

        sender_out = "X" * len(sender) if is_phone_number(sender) else sender.strip()
        notes = ["Auto-filled: check the masking and fields"]
        if not bank:
            notes.append("Unknown sender: add the bank name")
        rows.append([
            today, country, source, sender_out, bank, masked, txn_type, amount, currency,
            direction, merchant_of(masked, txn_type), edge_note(masked, txn_type, country, currency),
            "Yes", consent, name, "; ".join(notes),
        ])
    return rows, dropped


def main(argv=None):
    p = argparse.ArgumentParser(description="Turn an SMS export into masked rows for the 'SMS samples' tab.")
    p.add_argument("input", help="SMS Backup & Restore .xml, a .csv, or a .txt file")
    p.add_argument("-o", "--output", default="sms_rows.csv", help="CSV to write (default: sms_rows.csv)")
    p.add_argument("--name", required=True, help="Your name for the 'Collected by' column")
    p.add_argument("--consent", choices=["Yes", "No"], default="Yes",
                   help="Owner consent: Yes if these are your own messages (default Yes)")
    p.add_argument("--source", default="SMS", choices=["SMS", "App notification", "Email alert", "Statement line", "Screenshot"])
    p.add_argument("--date", default=dt.date.today().isoformat(), help="Date collected (default: today)")
    p.add_argument("--per-bank-type", type=int, default=10,
                   help="Max rows per bank and transaction type, for variety (0 = no limit; default 10)")
    p.add_argument("--keep-unknown", action="store_true",
                   help="Keep alerts from unrecognised sender IDs (never from personal phone numbers)")
    p.add_argument("--preview", type=int, default=0, help="Also print the first N rows")
    a = p.parse_args(argv)

    if Path(a.output).resolve() == Path(a.input).resolve():
        raise SystemExit("Output must be a different file from the input.")
    rows, dropped = process(read_messages(a.input), a.name, a.consent, a.source, a.date,
                            a.per_bank_type, a.keep_unknown)
    with open(a.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows)          # no header: paste/import at column B of a data row

    by_country = Counter(r[1] for r in rows)
    by_bank = Counter(r[4] or "(unknown)" for r in rows)
    by_type = Counter(r[6] for r in rows)
    print(f"Wrote {len(rows)} masked rows to {a.output}")
    print("  By country: " + ", ".join(f"{k} {v}" for k, v in by_country.most_common()))
    print("  By bank:    " + ", ".join(f"{k} {v}" for k, v in by_bank.most_common()))
    print("  By type:    " + ", ".join(f"{k} {v}" for k, v in by_type.most_common()))
    print("Skipped: " + (", ".join(f"{k} {v}" for k, v in dropped.most_common()) or "none"))
    for r in rows[: a.preview]:
        print(f"\n[{r[1]} | {r[4]} | {r[6]} | {r[7]} {r[8]} | {r[9]} | {r[10]}]\n  {r[5]}")
    print("\nNext: read every row, fix anything wrong, then import at cell B4 (or the first empty row)\n"
          "of 'SMS samples' with File > Import > Upload > 'Replace data at selected cell'.")


if __name__ == "__main__":
    sys.exit(main())
