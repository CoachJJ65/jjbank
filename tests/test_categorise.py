from execution.categorise import categorise_transaction, categorise_many


def test_groceries():
    assert categorise_transaction("groceries at Tesco") == "groceries"
    assert categorise_transaction("Sainsbury weekly shop") == "groceries"


def test_transport():
    assert categorise_transaction("Bus fare") == "transport"
    assert categorise_transaction("Train ticket") == "transport"
    assert categorise_transaction("Metro tap") == "transport"
    assert categorise_transaction("Fuel at Shell") == "transport"
    assert categorise_transaction("Taxi ride") == "transport"
    assert categorise_transaction("Uber to work") == "transport"


def test_bills():
    assert categorise_transaction("Electricity bill") == "bills"
    assert categorise_transaction("Gas bill") == "bills"
    assert categorise_transaction("Water bill") == "bills"
    assert categorise_transaction("Internet bill") == "bills"
    assert categorise_transaction("Phone bill") == "bills"


def test_eating_out():
    assert categorise_transaction("Restaurant dinner") == "eating_out"
    assert categorise_transaction("McDonald's lunch") == "eating_out"
    assert categorise_transaction("Pizza takeaway") == "eating_out"
    assert categorise_transaction("Cafe coffee") == "eating_out"
    assert categorise_transaction("Deliveroo order") == "eating_out"


def test_entertainment():
    assert categorise_transaction("Cinema tickets") == "entertainment"
    assert categorise_transaction("Monthly Netflix") == "entertainment"
    assert categorise_transaction("Spotify subscription") == "entertainment"
    assert categorise_transaction("Game purchase") == "entertainment"
    assert categorise_transaction("Concert tickets") == "entertainment"


def test_shopping():
    assert categorise_transaction("Amazon order") == "shopping"
    assert categorise_transaction("eBay sweater") == "shopping"
    assert categorise_transaction("Argos electronics") == "shopping"
    assert categorise_transaction("New shoes") == "shopping"
    assert categorise_transaction("Clothes shopping") == "shopping"


def test_subscriptions():
    assert categorise_transaction("Monthly gym membership") == "subscriptions"
    assert categorise_transaction("Annual software plan") == "subscriptions"
    assert categorise_transaction("Recurring subscription") == "subscriptions"


def test_rent_mortgage():
    assert categorise_transaction("Monthly rent payment") == "rent_mortgage"
    assert categorise_transaction("Mortgage repayment") == "rent_mortgage"
    assert categorise_transaction("Housing association") == "rent_mortgage"


def test_uncategorised_fallback():
    assert categorise_transaction("Miscellaneous bank fee") == "uncategorised"
    assert categorise_transaction("Random transfer") == "uncategorised"


def test_case_insensitive():
    assert categorise_transaction("GROCERIES shopping") == "groceries"
    assert categorise_transaction("NETFLIX monthly") == "entertainment"


def test_categorise_many_counts_categories_and_uncategorised():
    rows = [
        {"id": 1, "description": "Tesco", "amount": -50, "side": "out"},
        {"id": 2, "description": "Uber", "amount": -20, "side": "out"},
        {"id": 3, "description": "Utilities bill", "amount": -30, "side": "out"},
        {"id": 4, "description": "Mystery charge", "amount": -10, "side": "out"},
        {"id": 5, "description": "Uber eats", "amount": -15, "side": "in"},
    ]
    result = categorise_many(rows)
    assert result["counts"] == {"groceries": 1, "transport": 1, "bills": 1, "uncategorised": 1}
    assert result["uncategorised_ids"] == [4]


def test_categorise_many_ignores_inflows_and_missing_ids():
    rows = [
        {"id": 1, "description": "Tesco", "amount": -50, "side": "out"},
        {"description": "Mystery charge", "amount": -10, "side": "out"},
    ]
    result = categorise_many(rows)
    assert result["counts"] == {"groceries": 1, "uncategorised": 1}
    assert result["uncategorised_ids"] == [None]
