"""Aggregate transactions into investment / expense summaries in USD, AED, INR."""

import csv
from collections import defaultdict

from .rates import CURRENCIES

KINDS = ("income", "expense", "investment", "redemption")


def _zero():
    return {c: 0.0 for c in CURRENCIES}


def _add(acc, values):
    for c in CURRENCIES:
        acc[c] += values[c]


def summarize(transactions, converter):
    totals = {k: _zero() for k in KINDS}
    counts = defaultdict(int)
    by_category = defaultdict(_zero)          # (kind, category) -> amounts
    by_month = defaultdict(lambda: {k: _zero() for k in KINDS})
    by_source_currency = defaultdict(lambda: defaultdict(float))  # kind -> cur -> amt

    for t in transactions:
        vals = converter.all_currencies(t.amount, t.currency)
        _add(totals[t.kind], vals)
        counts[t.kind] += 1
        _add(by_category[(t.kind, t.category)], vals)
        _add(by_month[t.month][t.kind], vals)
        by_source_currency[t.kind][t.currency] += t.amount

    net = {
        c: totals["income"][c] + totals["redemption"][c]
        - totals["expense"][c] - totals["investment"][c]
        for c in CURRENCIES
    }
    return {
        "totals": totals,
        "counts": dict(counts),
        "by_category": dict(by_category),
        "by_month": dict(sorted(by_month.items())),
        "by_source_currency": {k: dict(v) for k, v in by_source_currency.items()},
        "net": net,
    }


def _fmt(n):
    return f"{n:,.2f}"


def _table(headers, rows):
    widths = [len(h) for h in headers]
    for r in rows:
        widths = [max(w, len(str(c))) for w, c in zip(widths, r)]
    line = "  ".join("{:<%d}" % widths[0] if i == 0 else "{:>%d}" % w
                     for i, w in enumerate(widths))
    out = [line.format(*headers), "  ".join("-" * w for w in widths)]
    out += [line.format(*r) for r in rows]
    return "\n".join(out)


def render_text(summary, converter, by_month=False):
    hdr = ["", "Count", "USD", "AED", "INR"]
    r = converter.rates
    parts = [
        f"Rates used: 1 USD = {r['AED']} AED = {r['INR']} INR "
        f"(1 AED = {r['INR'] / r['AED']:.4f} INR)",
        "",
        "== Overall ==",
    ]
    labels = {
        "income": "Income", "expense": "Expenses",
        "investment": "Investments", "redemption": "Redemptions",
    }
    rows = []
    for k in KINDS:
        t = summary["totals"][k]
        rows.append([labels[k], summary["counts"].get(k, 0)] + [_fmt(t[c]) for c in CURRENCIES])
    rows.append(["Net cash flow", ""] + [_fmt(summary["net"][c]) for c in CURRENCIES])
    parts.append(_table(hdr, rows))

    spend = summary["totals"]["expense"]["USD"] + summary["totals"]["investment"]["USD"]
    if spend:
        pct = summary["totals"]["investment"]["USD"] / spend * 100
        parts.append(f"\nInvested {pct:.1f}% of all outgoing money (expenses + investments).")

    for kind in ("investment", "expense"):
        cats = sorted(
            ((cat, v) for (k, cat), v in summary["by_category"].items() if k == kind),
            key=lambda x: -x[1]["USD"],
        )
        if not cats:
            continue
        parts += ["", f"== {labels[kind]} by category =="]
        parts.append(_table(["Category", "USD", "AED", "INR"],
                            [[cat] + [_fmt(v[c]) for c in CURRENCIES] for cat, v in cats]))

    src = summary["by_source_currency"]
    if src:
        parts += ["", "== As charged (original currency) =="]
        rows = []
        for k in KINDS:
            if k in src:
                rows.append([labels[k]] + [_fmt(src[k].get(c, 0)) for c in CURRENCIES])
        parts.append(_table(["", "USD", "AED", "INR"], rows))

    if by_month and summary["by_month"]:
        parts += ["", "== Monthly (in AED / INR) =="]
        rows = []
        for month, kinds in summary["by_month"].items():
            rows.append([
                month,
                _fmt(kinds["expense"]["AED"]), _fmt(kinds["investment"]["AED"]),
                _fmt(kinds["expense"]["INR"]), _fmt(kinds["investment"]["INR"]),
            ])
        parts.append(_table(
            ["Month", "Expense AED", "Invest AED", "Expense INR", "Invest INR"], rows))

    return "\n".join(parts)


def write_csv(transactions, converter, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "kind", "category", "amount", "currency",
                    "USD", "AED", "INR", "sender", "message"])
        for t in transactions:
            v = converter.all_currencies(t.amount, t.currency)
            w.writerow([
                t.date.strftime("%Y-%m-%d") if t.date else "",
                t.kind, t.category, f"{t.amount:.2f}", t.currency,
                f"{v['USD']:.2f}", f"{v['AED']:.2f}", f"{v['INR']:.2f}",
                t.sender, t.body,
            ])
