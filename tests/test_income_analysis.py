from execution.income_analysis import analyse_income


def test_recurring_depositor_no_gaps():
    rows = [
        {"date": "2026-01-10", "title": "Income from Alan", "amount": 100, "side": "in"},
        {"date": "2026-02-15", "title": "Income from Alan", "amount": 100, "side": "in"},
        {"date": "2026-03-20", "title": "Income from Alan", "amount": 100, "side": "in"},
        {"date": "2026-03-25", "title": "Groceries", "amount": -50, "side": "out"},
    ]
    result = analyse_income(rows)

    assert result["monthly_depositors"] == ["Alan"]
    assert result["alerts"] == []


def test_recurring_depositor_missing_month_alert():
    rows = [
        {"date": "2026-01-10", "title": "Income from Beth", "amount": 100, "side": "in"},
        {"date": "2026-02-15", "title": "Income from Beth", "amount": 100, "side": "in"},
        {"date": "2026-03-25", "title": "Groceries", "amount": -50, "side": "out"},
    ]
    result = analyse_income(rows)

    assert result["monthly_depositors"] == ["Beth"]
    assert result["alerts"] == [{"name": "Beth", "month": "2026-03", "flags": ["missing"]}]
