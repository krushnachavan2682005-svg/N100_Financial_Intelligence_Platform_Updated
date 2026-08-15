import math

import pytest

from src.analytics.cagr import (
    CAGR_FLAG_BOTH_NEGATIVE,
    CAGR_FLAG_DECLINE_TO_LOSS,
    CAGR_FLAG_INSUFFICIENT,
    CAGR_FLAG_TURNAROUND,
    CAGR_FLAG_ZERO_BASE,
    calculate_cagr,
    calculate_cagr_from_series,
    calculate_cagr_with_flag,
    classify_cagr_edge_case,
)


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
    assert calculate_cagr_from_series([100, 161.051], num_years=5) == pytest.approx(
        0.10
    )


@pytest.mark.parametrize("values", [None, [], [100], [100, 0]])
def test_calculate_cagr_from_series_returns_none_for_insufficient_or_invalid_values(
    values,
):
    assert calculate_cagr_from_series(values) is None


@pytest.mark.parametrize(
    ("start_value", "end_value", "years", "expected_flag"),
    [
        (100, -50, 3, CAGR_FLAG_DECLINE_TO_LOSS),
        (-100, 50, 3, CAGR_FLAG_TURNAROUND),
        (-100, -50, 3, CAGR_FLAG_BOTH_NEGATIVE),
        (0, 100, 3, CAGR_FLAG_ZERO_BASE),
        (100, 0, 3, CAGR_FLAG_ZERO_BASE),
        (None, 100, 3, CAGR_FLAG_INSUFFICIENT),
        (100, 121, 0, CAGR_FLAG_INSUFFICIENT),
    ],
)
def test_classify_cagr_edge_case(start_value, end_value, years, expected_flag):
    assert classify_cagr_edge_case(start_value, end_value, years) == expected_flag


def test_calculate_cagr_with_flag_returns_value_and_no_flag_for_valid_inputs():
    cagr, flag = calculate_cagr_with_flag(100, 121, 2)
    assert cagr == pytest.approx(0.10)
    assert flag is None


def test_calculate_cagr_with_flag_returns_flag_for_edge_cases():
    cagr, flag = calculate_cagr_with_flag(100, -50, 3)
    assert cagr is None
    assert flag == CAGR_FLAG_DECLINE_TO_LOSS
