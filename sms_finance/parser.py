"""Parse bank / broker SMS alerts into transactions.

Handles the common formats sent by UAE banks (Emirates NBD, ADCB, FAB,
Mashreq, ...), Indian banks (HDFC, ICICI, SBI, Axis, ...) and brokers / fund
platforms (Zerodha, Groww, IBKR, Sarwa, ...).
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# --- amount + currency -------------------------------------------------------

_NUM = r"(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_CUR_PREFIX = r"(AED|Dhs\.?|DHS|INR|Rs\.?|₹|USD|US\$|\$)"
_CUR_SUFFIX = r"(AED|INR|USD|Dhs|DHS)\b"

_PREFIX_RE = re.compile(_CUR_PREFIX + r"\s*" + _NUM, re.IGNORECASE)
_SUFFIX_RE = re.compile(_NUM + r"\s*" + _CUR_SUFFIX, re.IGNORECASE)

_CUR_MAP = {
    "aed": "AED", "dhs": "AED", "dhs.": "AED",
    "inr": "INR", "rs": "INR", "rs.": "INR", "₹": "INR",
    "usd": "USD", "us$": "USD", "$": "USD",
}

# Amounts preceded by these words are balances / limits, not the transaction.
_IGNORE_CONTEXT = re.compile(
    r"(bal(ance)?|avl|avail(able)?|limit|outstanding|min(imum)?\s+due|total\s+due)"
    r"[\s:.\-a-z]*$",
    re.IGNORECASE,
)

# --- classification keywords -------------------------------------------------

_SKIP = re.compile(r"\b(otp|one[\s-]?time\s+password|verification\s+code)\b", re.I)

_INVESTMENT = re.compile(
    r"\b(sip|mutual\s*funds?|\bmf\b|zerodha|groww|upstox|kuvera|coin\s+by|"
    r"paytm\s+money|angel\s*one|smallcase|demat|nps|ppf|sgb|sovereign\s+gold|"
    r"fixed\s+deposit|\bfd\b|recurring\s+deposit|\brd\b|ibkr|interactive\s+brokers|"
    r"sarwa|etoro|stake|wahed|baraka|stocks?|shares|equity|invest(ment|ed)?|"
    r"brokerage|trading\s+a/?c)\b",
    re.IGNORECASE,
)

_DEBIT = re.compile(
    r"\b(debited|debit|spent|purchase[d]?|paid|payment\s+of|withdrawn|withdrawal|"
    r"sent|transferred\s+to|charged|txn\s+of|pos|used\s+for|deducted)\b",
    re.IGNORECASE,
)
_CREDIT = re.compile(
    r"\b(credited|credit(?!\s*card)|received|deposited|salary|refund(ed)?|"
    r"reversed|cashback|redeemed|redemption)\b",
    re.IGNORECASE,
)

EXPENSE_CATEGORIES = [
    ("Food", r"swiggy|zomato|talabat|deliveroo|careem\s*food|noon\s*food|restaurant|"
             r"cafe|coffee|starbucks|mcdonald|kfc|domino|pizza|eatery"),
    ("Groceries", r"carrefour|lulu|spinneys|waitrose|union\s*coop|choithrams|"
                  r"bigbasket|blinkit|zepto|dmart|grocer|supermarket|instamart"),
    ("Transport", r"uber|careem|\bola\b|rapido|rta|salik|nol|metro|taxi|enoc|adnoc|"
                  r"eppco|petrol|fuel|parking|indian\s*oil|hpcl|bpcl"),
    ("Shopping", r"amazon|noon|flipkart|myntra|ajio|namshi|ikea|mall|shein"),
    ("Bills & Utilities", r"dewa|sewa|addc|etisalat|\be&\b|\bdu\b|airtel|jio|"
                          r"vodafone|\bvi\b|bsnl|electricity|water\s+bill|"
                          r"broadband|recharge|postpaid|dth|gas\s+bill"),
    ("Rent & Housing", r"\brent\b|ejari|maintenance|society|landlord"),
    ("Cash", r"\batm\b|cash\s+withdrawal"),
    ("Travel", r"emirates|flydubai|air\s*arabia|indigo|air\s*india|vistara|"
               r"booking\.com|airbnb|makemytrip|hotel|airline"),
    ("Entertainment", r"netflix|spotify|prime\s*video|hotstar|youtube|apple\.com|"
                      r"google\s*play|cinema|vox|pvr|inox|bookmyshow"),
    ("Health", r"pharmacy|aster|hospital|clinic|apollo|medical|life\s*pharmacy"),
    ("Education", r"school|tuition|college|university|udemy|coursera|fees"),
    ("Transfers", r"remit|exchange|western\s*union|al\s*ansari|lulu\s*exchange|"
                  r"wise|neft|imps|rtgs|upi|transferred\s+to"),
]
_EXPENSE_RES = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in EXPENSE_CATEGORIES]

# --- dates inside the message body ------------------------------------------

_DATE_PATTERNS = [
    (re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{2,4})\b"), ("%d-%b-%y", "%d-%b-%Y")),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b"), ("%d/%m/%y", "%d/%m/%Y")),
    (re.compile(r"\b(\d{1,2}-\d{1,2}-\d{2,4})\b"), ("%d-%m-%y", "%d-%m-%Y")),
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), ("%Y-%m-%d",)),
    (re.compile(r"\b(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\b"), ("%d %b %Y",)),
    (re.compile(r"\b(\d{1,2}[A-Za-z]{3}\d{2,4})\b"), ("%d%b%y", "%d%b%Y")),
]


@dataclass
class Transaction:
    body: str
    amount: float
    currency: str
    kind: str                 # "expense" | "investment" | "income" | "redemption"
    category: str
    date: Optional[datetime] = None
    sender: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def month(self):
        return self.date.strftime("%Y-%m") if self.date else "unknown"


def _to_float(num):
    return float(num.replace(",", ""))


def extract_amount(body):
    """Return (amount, currency) for the transaction amount in an SMS, or None."""
    candidates = []
    for m in _PREFIX_RE.finditer(body):
        candidates.append((m.start(), m.group(1), m.group(2)))
    for m in _SUFFIX_RE.finditer(body):
        candidates.append((m.start(), m.group(2), m.group(1)))
    candidates.sort(key=lambda c: c[0])

    for start, cur, num in candidates:
        before = body[max(0, start - 30):start]
        if _IGNORE_CONTEXT.search(before):
            continue
        currency = _CUR_MAP.get(cur.lower())
        if not currency:
            continue
        amount = _to_float(num)
        if amount <= 0:
            continue
        return amount, currency
    return None


def extract_date(body):
    for regex, fmts in _DATE_PATTERNS:
        m = regex.search(body)
        if not m:
            continue
        for fmt in fmts:
            try:
                return datetime.strptime(m.group(1), fmt)
            except ValueError:
                continue
    return None


def classify(body):
    """Return (kind, category) or None if the SMS is not a money movement."""
    is_debit = bool(_DEBIT.search(body))
    is_credit = bool(_CREDIT.search(body))
    is_invest = bool(_INVESTMENT.search(body))

    # Whichever direction word appears first wins when both are present
    # ("debited ... and credited to beneficiary").
    if is_debit and is_credit:
        d = _DEBIT.search(body).start()
        c = _CREDIT.search(body).start()
        is_debit, is_credit = d <= c, c < d

    if is_invest:
        if is_credit:
            return "redemption", "Investment redemption"
        return "investment", _investment_category(body)

    if is_credit:
        if re.search(r"salary", body, re.I):
            return "income", "Salary"
        if re.search(r"refund|reversed|cashback", body, re.I):
            return "income", "Refund / Cashback"
        return "income", "Other income"

    if is_debit:
        for name, regex in _EXPENSE_RES:
            if regex.search(body):
                return "expense", name
        return "expense", "Other expense"

    return None


def _investment_category(body):
    b = body.lower()
    if re.search(r"\bsip\b|mutual\s*fund|\bmf\b|kuvera|coin\s+by|groww", b):
        return "Mutual funds / SIP"
    if re.search(r"fixed\s+deposit|\bfd\b|recurring\s+deposit|\brd\b", b):
        return "Fixed / recurring deposit"
    if re.search(r"\bnps\b|\bppf\b", b):
        return "NPS / PPF"
    if re.search(r"gold|sgb", b):
        return "Gold"
    return "Stocks / brokerage"


def parse_message(body, date=None, sender=""):
    """Turn one SMS into a Transaction, or None if it isn't one."""
    if not body or _SKIP.search(body):
        return None
    amt = extract_amount(body)
    if not amt:
        return None
    cls = classify(body)
    if not cls:
        return None
    amount, currency = amt
    kind, category = cls
    return Transaction(
        body=body.strip(),
        amount=amount,
        currency=currency,
        kind=kind,
        category=category,
        date=date or extract_date(body),
        sender=sender,
    )
