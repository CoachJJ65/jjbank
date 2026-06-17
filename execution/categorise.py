_RULES = [
    ("groceries", ["groceries", "supermarket", "tesco", "sainsbury", "aldi", "lidl", "asda", "morrisons"]),
    ("transport", ["bus", "train", "metro", "fuel", "taxi", "fare", "uber", "lyft", "shell", "bp ", "ess ", "parking"]),
    ("bills", ["bill", "electricity", "gas", "water", "internet", "phone", "council tax", "utilities"]),
    ("eating_out", ["restaurant", "mcdonald", "pizza", "cafe", "coffee", "deliveroo", "uber eats", "takeaway", "pub", "bar"]),
    ("entertainment", ["cinema", "netflix", "spotify", "game", "concert", "spotify", "netflix", "amazon prime"]),
    ("shopping", ["amazon", "ebay", "argos", "primark", "next", "matalan", "asos", "zara", "clothes", "shoes"]),
    ("subscriptions", ["subscription", "membership", "gym", "fitness", "recurring", "software"]),
    ("rent_mortgage", ["rent", "mortgage", "housing", "landlord", "lease"]),
]


def categorise_transaction(description: str) -> str:
    lookup = description.lower()
    for category, keywords in _RULES:
        if any(keyword in lookup for keyword in keywords):
            return category
    return "uncategorised"


def categorise_many(rows):
    counts = {}
    uncategorised_ids = []

    for row in rows:
        if row.get("side") != "out":
            continue

        category = categorise_transaction(row.get("description", ""))
        counts[category] = counts.get(category, 0) + 1

        if category == "uncategorised":
            uncategorised_ids.append(row.get("id"))

    return {
        "counts": counts,
        "uncategorised_ids": uncategorised_ids,
    }
