from collections import defaultdict
from pathlib import Path

from execution.categorise import categorise_transaction


def classify(description: str) -> str:
    return categorise_transaction(description)


def spending_summary(rows):
    categories = defaultdict(float)
    for row in rows:
        if row.get("side") == "out":
            category = classify(row.get("description", ""))
            categories[category] += abs(row.get("amount", 0.0))

    result = {category: round(total, 2) for category, total in categories.items()}
    total_out = round(sum(result.values()), 2)
    return {"categories": result, "total_out": total_out}


def spending_breakdown(rows):
    totals = defaultdict(float)
    uncategorised_ids = []

    for row in rows:
        if row.get("side") != "out":
            continue

        category = classify(row.get("description", ""))
        totals[category] += abs(row.get("amount", 0.0))

        if category == "uncategorised":
            uncategorised_ids.append(row.get("id"))

    totals_out = round(sum(totals.values()), 2)
    return {
        "totals": {category: round(total, 2) for category, total in totals.items()},
        "total_out": totals_out,
        "uncategorised_count": len(uncategorised_ids),
        "uncategorised_transaction_ids": uncategorised_ids,
    }


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

    spend_summary = spending_summary(rows)
    spend_breakdown = spending_breakdown(rows)
    totals = money_totals(rows)
    income = analyse_income(rows)
    return {
        "money_in_out": totals,
        "income_analysis": income,
        "spending_summary": spend_summary,
        "spending_breakdown": spend_breakdown,
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

    lines.append("## Uncategorised Transactions")
    lines.append("")
    spend_breakdown = report.get("spending_breakdown", {})
    uncategorised_count = spend_breakdown.get("uncategorised_count", 0)
    uncategorised_ids = spend_breakdown.get("uncategorised_transaction_ids", [])
    if uncategorised_count > 0 or uncategorised_ids:
        lines.append(f"- Uncategorised Transactions: {uncategorised_count}")
        if uncategorised_ids:
            lines.append(f"- Uncategorised Transaction IDs: {uncategorised_ids}")
    else:
        lines.append("- None")
    lines.append("")

    return "\n".join(lines)
