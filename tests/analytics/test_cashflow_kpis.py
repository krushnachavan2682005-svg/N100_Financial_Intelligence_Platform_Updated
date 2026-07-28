import math

import pytest

from src.analytics.cashflow_kpis import (
    CAPITAL_ALLOCATION_PATTERNS,
    cash_flow_sign,
    classify_capital_allocation,
    cfo_to_ebitda,
    cfo_to_operating_profit,
    fcf_to_net_profit,
    free_cash_flow,
)


def test_free_cash_flow_deducts_positive_capex():
    assert free_cash_flow(500, 150) == 350.0


def test_free_cash_flow_normalizes_negative_cash_flow_capex():
    assert free_cash_flow(500, -150) == 350.0


def test_free_cash_flow_can_be_negative():
    assert free_cash_flow(100, 150) == -50.0


def test_free_cash_flow_with_zero_capex_equals_operating_cash_flow():
    assert free_cash_flow(250, 0) == 250.0


@pytest.mark.parametrize("cfo, capex", [(None, 100), (100, None), ("unknown", 100), (100, math.nan)])
def test_free_cash_flow_returns_none_for_missing_or_invalid_metrics(cfo, capex):
    assert free_cash_flow(cfo, capex) is None


@pytest.mark.parametrize(
    ("function", "numerator", "denominator", "expected"),
    [
        (fcf_to_net_profit, 350, 200, 1.75),
        (cfo_to_ebitda, 500, 625, 0.8),
        (cfo_to_operating_profit, 500, 400, 1.25),
    ],
)
def test_cash_flow_ratios_calculate_expected_values(function, numerator, denominator, expected):
    assert function(numerator, denominator) == expected


@pytest.mark.parametrize("function", [fcf_to_net_profit, cfo_to_ebitda, cfo_to_operating_profit])
def test_cash_flow_ratios_return_none_for_zero_denominator(function):
    assert function(100, 0) is None


@pytest.mark.parametrize("function", [fcf_to_net_profit, cfo_to_ebitda, cfo_to_operating_profit])
def test_cash_flow_ratios_return_none_for_missing_metrics(function):
    assert function(None, 100) is None
    assert function(100, None) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [(500, "+"), (-150, "-"), (0, "0"), (None, None)],
)
def test_cash_flow_sign(value, expected):
    assert cash_flow_sign(value) == expected


@pytest.mark.parametrize(
    ("cfo", "cfi", "cff", "expected_label"),
    [
        (100, -50, -25, "Reinvestor"),
        (-100, 50, 25, "Distress Signal"),
        (100, 50, -25, "Debt Repayer"),
        (100, -50, 25, "Growth Financier"),
        (-100, -50, 25, "Startup Financier"),
        (-100, 50, -25, "Restructuring"),
        (-100, -50, -25, "Cash Burn"),
        (100, 50, 25, "Cash Accumulator"),
    ],
)
def test_classify_capital_allocation_maps_eight_patterns(cfo, cfi, cff, expected_label):
    result = classify_capital_allocation(cfo, cfi, cff)
    assert result["pattern_label"] == expected_label
    assert (result["cfo_sign"], result["cfi_sign"], result["cff_sign"]) in CAPITAL_ALLOCATION_PATTERNS


def test_classify_capital_allocation_marks_missing_inputs_as_incomplete():
    result = classify_capital_allocation(100, None, -25)
    assert result["pattern_label"] == "Incomplete"
