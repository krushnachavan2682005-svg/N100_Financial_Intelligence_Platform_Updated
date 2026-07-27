import math

import pytest

from src.analytics.cashflow_kpis import (
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
