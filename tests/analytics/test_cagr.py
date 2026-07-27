import math

import pytest

from src.analytics.cagr import calculate_cagr, calculate_cagr_from_series


def test_calculate_cagr_for_positive_growth():
    assert calculate_cagr(100, 121, 2) == pytest.approx(0.10)


@pytest.mark.parametrize(
    ("start_value", "end_value", "years", "expected"),
    [
        (100, 133.1, 3, 0.10),
        (100, 161.051, 5, 0.10),
        (250, 250, 3, 0.0),
    ],
)
def test_calculate_cagr_for_multi_year_spans(start_value, end_value, years, expected):
    assert calculate_cagr(start_value, end_value, years) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("start_value", "end_value", "years"),
    [
        (0, 100, 3),
        (-100, 100, 3),
        (100, 0, 3),
        (100, -120, 3),
        (100, 121, 0),
        (100, 121, -2),
        (None, 121, 2),
        (100, None, 2),
        (100, 121, None),
        (100, math.inf, 2),
    ],
)
def test_calculate_cagr_returns_none_for_invalid_inputs(start_value, end_value, years):
    assert calculate_cagr(start_value, end_value, years) is None


def test_calculate_cagr_from_annual_series_uses_observation_span():
    assert calculate_cagr_from_series([100, 110, 121, 133.1]) == pytest.approx(0.10)


def test_calculate_cagr_from_series_accepts_an_explicit_period():
    assert calculate_cagr_from_series([100, 161.051], num_years=5) == pytest.approx(0.10)


@pytest.mark.parametrize("values", [None, [], [100], [100, 0]])
def test_calculate_cagr_from_series_returns_none_for_insufficient_or_invalid_values(values):
    assert calculate_cagr_from_series(values) is None
