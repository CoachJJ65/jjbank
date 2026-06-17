import re
from collections import defaultdict


_IN_PREFIXES = ("Income from", "Transfer from", "Deposit from")


def _derive_name(title: str):
    for prefix in _IN_PREFIXES:
        pattern = re.compile(re.escape(prefix), re.IGNORECASE)
        match = pattern.search(title)
        if match:
            start = match.end()
            name = title[start:].strip()
            return ' '.join(name.split())
    return None


def _ym(date: str):
    if len(date) >= 7:
        return date[:7]
    return None


def analyse_income(rows):
    all_months = set()
    for row in rows:
        month = _ym(row.get("date", ""))
        if month:
            all_months.add(month)

    per_payer_months = defaultdict(set)
    for row in rows:
        if row.get("side") != "in":
            continue
        name = _derive_name(row.get("title", ""))
        if not name:
            continue
        month = _ym(row.get("date", ""))
        if not month:
            continue
        per_payer_months[name].add(month)

    monthly_depositors = sorted(
        name for name, months in per_payer_months.items() if len(months) >= 2
    )

    if not all_months:
        return {"monthly_depositors": monthly_depositors, "alerts": []}

    min_month = min(all_months)
    max_month = max(all_months)

    month_range = set()
    year, month = int(min_month[:4]), int(min_month[5:7])
    while (year, month) <= (int(max_month[:4]), int(max_month[5:7])):
        month_range.add(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1

    alerts = []
    for name, months in sorted(per_payer_months.items()):
        for month in sorted(month_range - months):
            alerts.append({"name": name, "month": month, "flags": ["missing"]})

    return {"monthly_depositors": monthly_depositors, "alerts": alerts}
