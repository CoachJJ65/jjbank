from execution.reports import spending_summary, spending_breakdown


def test_spending_summary_groups_by_category():
    rows = [
        {"date": "2024-01-01", "description": "Tesco groceries", "amount": -90, "side": "out"},
        {"date": "2024-01-02", "description": "Uber trip", "amount": -20, "side": "out"},
        {"date": "2024-01-03", "description": "Shell fuel", "amount": -35, "side": "out"},
    ]
    result = spending_summary(rows)

    assert result["categories"]["transport"] == 55
    assert result["categories"]["groceries"] == 90
    assert result["total_out"] == 145


def test_spending_summary_empty_rows():
    assert spending_summary([]) == {"categories": {}, "total_out": 0}


def test_spending_summary_ignores_inflows():
    rows = [
        {"date": "2024-01-01", "description": "Tesco", "amount": -10, "side": "out"},
        {"date": "2024-01-01", "description": "Salary", "amount": 100, "side": "in"},
    ]
    result = spending_summary(rows)

    assert result["categories"]["groceries"] == 10
    assert result["total_out"] == 10


def test_spending_breakdown_totals_and_uncategorised_count():
    rows = [
        {"date": "2024-01-01", "description": "Tesco", "amount": -10, "side": "out", "id": 1},
        {"date": "2024-01-02", "description": "Uber", "amount": -20, "side": "out", "id": 2},
        {"date": "2024-01-03", "description": "Unknown charge", "amount": -5, "side": "out", "id": 3},
        {"date": "2024-01-03", "description": "Salary", "amount": 100, "side": "in"},
    ]
    result = spending_breakdown(rows)

    assert result["total_out"] == 35
    assert result["totals"]["transport"] == 20
    assert result["totals"]["groceries"] == 10
    assert result["totals"]["uncategorised"] == 5
    assert result["uncategorised_count"] == 1
    assert result["uncategorised_transaction_ids"] == [3]


def test_spending_breakdown_empty_rows():
    assert spending_breakdown([]) == {"totals": {}, "total_out": 0, "uncategorised_count": 0, "uncategorised_transaction_ids": []}
