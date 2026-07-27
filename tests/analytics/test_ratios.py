import math

import pytest

from src.analytics.ratios import (
    asset_turnover,
    current_ratio,
    debt_to_equity,
    interest_coverage,
    net_profit_margin,
    operating_profit_margin,
    return_on_capital_employed,
    return_on_equity,
)


@pytest.mark.parametrize(
    ("function", "numerator", "denominator", "expected"),
    [
        (operating_profit_margin, 250, 1_000, 25.0),
        (net_profit_margin, 120, 1_000, 12.0),
        (return_on_equity, 150, 750, 20.0),
        (return_on_capital_employed, 300, 1_500, 20.0),
        (asset_turnover, 1_200, 600, 2.0),
    ],
)
def test_ratios_calculate_expected_values(function, numerator, denominator, expected):
    assert function(numerator, denominator) == expected


@pytest.mark.parametrize(
    ("function", "numerator"),
    [
        (operating_profit_margin, 250),
        (net_profit_margin, 120),
        (return_on_equity, 150),
        (return_on_capital_employed, 300),
        (asset_turnover, 1_200),
    ],
)
def test_ratios_return_none_for_zero_denominator(function, numerator):
    assert function(numerator, 0) is None


@pytest.mark.parametrize(
    "missing_value",
    [None, "", "not available", float("nan"), math.inf],
)
def test_ratios_return_none_for_missing_or_non_finite_metrics(missing_value):
    assert operating_profit_margin(missing_value, 1_000) is None
    assert operating_profit_margin(250, missing_value) is None


def test_ratios_preserve_negative_profit_values():
    assert net_profit_margin(-50, 1_000) == -5.0
    assert return_on_equity(-75, 500) == -15.0


@pytest.mark.parametrize(
    ("function", "numerator", "denominator", "expected"),
    [
        (debt_to_equity, 300, 600, 0.5),
        (interest_coverage, 450, 90, 5.0),
        (current_ratio, 1_200, 800, 1.5),
    ],
)
def test_solvency_and_liquidity_ratios_calculate_expected_values(function, numerator, denominator, expected):
    assert function(numerator, denominator) == expected


def test_debt_to_equity_reports_high_leverage():
    assert debt_to_equity(2_000, 500) == 4.0


@pytest.mark.parametrize(
    ("function", "numerator"),
    [
        (debt_to_equity, 300),
        (interest_coverage, 450),
        (current_ratio, 1_200),
    ],
)
def test_solvency_and_liquidity_ratios_return_none_for_zero_denominator(function, numerator):
    assert function(numerator, 0) is None


@pytest.mark.parametrize("function", [debt_to_equity, interest_coverage, current_ratio])
def test_solvency_and_liquidity_ratios_return_none_for_missing_metrics(function):
    assert function(None, 100) is None
    assert function(100, None) is None
