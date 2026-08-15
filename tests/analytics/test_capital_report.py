from src.analytics.capital_report import get_pattern_label


def test_get_pattern_label():
    # Consistent Compounder (+, -, -)
    assert get_pattern_label(100, -50, -20) == "Consistent Compounder"

    # Growth Phase (+, -, +)
    assert get_pattern_label(100, -50, 20) == "Growth Phase"

    # Start-up / Cash Burn (-, -, +)
    assert get_pattern_label(-100, -50, 100) == "Start-up / Cash Burn"

    # Severe Distress (-, +, +)
    assert get_pattern_label(-100, 50, 100) == "Severe Distress"

    # Distress & Debt Repayment (-, +, -)
    assert get_pattern_label(-100, 50, -100) == "Distress & Debt Repayment"

    # Divestment & Deleveraging (+, +, -)
    assert get_pattern_label(100, 50, -100) == "Divestment & Deleveraging"

    # Divestment & Expansion (+, +, +)
    assert get_pattern_label(100, 50, 100) == "Divestment & Expansion"

    # Liquidation (-, -, -)
    assert get_pattern_label(-100, -50, -50) == "Liquidation"

    # NaN cases
    assert get_pattern_label(None, -50, -20) == "Unknown"
