"""Load SMS messages from common export formats.

Supported:
  * .xml  - "SMS Backup & Restore" (Android) export
  * .csv  - any CSV with a body/message/text column (optional date, address)
  * .txt  - plain text; one message per line, or messages separated by blank lines
"""

import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

_BODY_COLS = ("body", "message", "text", "sms", "content")
_DATE_COLS = ("date", "datetime", "time", "timestamp", "received")
_SENDER_COLS = ("address", "sender", "from", "number")

_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d %b %Y", "%b %d, %Y %I:%M:%S %p",
)


def _parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    if value.isdigit():
        n = int(value)
        return datetime.fromtimestamp(n / 1000 if n > 10**11 else n)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def load_xml(path):
    root = ET.parse(path).getroot()
    for sms in root.iter("sms"):
        # type 1 = inbox; bank alerts are always received messages
        if sms.get("type") not in (None, "1"):
            continue
        yield sms.get("body", ""), _parse_date(sms.get("date")), sms.get("address", "")


def _pick(header, names):
    lower = {h.lower().strip(): h for h in header}
    for n in names:
        if n in lower:
            return lower[n]
    return None


def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        body_col = _pick(header, _BODY_COLS)
        if not body_col:
            raise ValueError(f"{path}: no body/message/text column in {header}")
        date_col = _pick(header, _DATE_COLS)
        sender_col = _pick(header, _SENDER_COLS)
        for row in reader:
            yield (
                row.get(body_col, ""),
                _parse_date(row.get(date_col)) if date_col else None,
                row.get(sender_col, "") if sender_col else "",
            )


def load_txt(path):
    text = Path(path).read_text(encoding="utf-8")
    chunks = [c.strip() for c in text.split("\n\n")] if "\n\n" in text else text.splitlines()
    for chunk in chunks:
        chunk = " ".join(chunk.split())
        if chunk:
            yield chunk, None, ""


def load(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".xml":
        return list(load_xml(path))
    if suffix == ".csv":
        return list(load_csv(path))
    return list(load_txt(path))
