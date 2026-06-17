from collections import defaultdict
from pathlib import Path

from execution.categorise import categorise_transaction


_FALLBACK_RULES = [
    ("transport", ["uber", "trip"]),
]


def _classify(description: str) -> str:
    category = categorise_transaction(description)
    if category != "uncategorised":
        return category
    lookup = description.lower()
    for category, keywords in _FALLBACK_RULES:
        if any(keyword in lookup for keyword in keywords):
            return category
    return "uncategorised"


def spending_summary(rows):
    categories = defaultdict(float)
    for row in rows:
        if row.get("side") == "out":
            category = _classify(row.get("description", ""))
            categories[category] += abs(row.get("amount", 0.0))

    result = {category: round(total, 2) for category, total in categories.items()}
    total_out = round(sum(result.values()), 2)
    return {"categories": result, "total_out": total_out}


def money_totals(rows):
    total_in = 0.0
    total_out = 0.0
    for row in rows:
        amount = float(row.get("amount", 0.0))
        if amount >= 0:
            total_in += amount
        else:
            total_out += abs(amount)
    return {
        "total_in": round(total_in, 2),
        "total_out": round(total_out, 2),
    }


def build_report(rows):
    from execution.income_analysis import analyse_income

    spend = spending_summary(rows)
    totals = money_totals(rows)
    income = analyse_income(rows)
    return {
        "money_in_out": totals,
        "income_analysis": income,
        "spending_summary": spend,
    }


def render_markdown(report: dict) -> str:
    lines = ["# jjbank Report", ""]
    lines.append("## Money In / Out")
    lines.append("")
    lines.append(f"- Money In:  {report['money_in_out'].get('total_in', 0):.2f}")
    lines.append(f"- Money Out: {report['money_in_out'].get('total_out', 0):.2f}")
    lines.append("")

    lines.append("## Recurring Depositors")
    lines.append("")
    depositors = report.get("income_analysis", {}).get("monthly_depositors", [])
    if depositors:
        for name in depositors:
            lines.append(f"- {name}")
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## Missing Payment Alerts")
    lines.append("")
    alerts = report.get("income_analysis", {}).get("alerts", [])
    if alerts:
        for alert in alerts:
            lines.append(f"- {alert['name']} missing in {alert['month']}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Spending by Category")
    lines.append("")
    lines.append("| Category | Amount |")
    lines.append("|----------|--------|")
    categories = report.get("spending_summary", {}).get("categories", {})
    for category, amount in sorted(categories.items()):
        lines.append(f"| {category} | {amount:.2f} |")
    lines.append("")
    lines.append(
        f"**Total Out:** {report.get('spending_summary', {}).get('total_out', 0):.2f}"
    )
    lines.append("")
    return "\n".join(lines)
