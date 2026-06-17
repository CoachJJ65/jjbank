_RULES = [
    ("groceries", ["groceries", "supermarket", "tesco", "sainsbury"]),
    ("transport", ["bus", "train", "metro", "fuel", "taxi", "fare"]),
    ("bills", ["bill", "electricity", "gas", "water", "internet", "phone"]),
]


def categorise_transaction(description: str) -> str:
    lookup = description.lower()
    for category, keywords in _RULES:
        if any(keyword in lookup for keyword in keywords):
            return category
    return "uncategorised"
