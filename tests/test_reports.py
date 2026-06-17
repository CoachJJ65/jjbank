from execution.reports import spending_summary


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
