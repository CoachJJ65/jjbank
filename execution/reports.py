from collections import defaultdict

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
