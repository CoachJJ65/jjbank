from execution.categorise import categorise_transaction


def test_keyword_rules_categorise_description():
    assert categorise_transaction("Weekly groceries at Tesco") == "groceries"
    assert categorise_transaction("Bus fare to work") == "transport"
    assert categorise_transaction("Monthly electricity bill") == "bills"
    assert categorise_transaction("Unknown restaurant") == "uncategorised"
    assert categorise_transaction("GROCERIES shopping") == "groceries"
