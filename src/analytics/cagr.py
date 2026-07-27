"""Compound annual growth rate utilities for annual financial time series."""

from __future__ import annotations

import math
from numbers import Real
from typing import Any, Sequence


def _as_positive_finite_number(value: Any) -> float | None:
    """Return a positive finite numeric value, or ``None`` for invalid inputs."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Real):
        number = float(value)
    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
    return number if math.isfinite(number) and number > 0 else None


def calculate_cagr(start_val: Any, end_val: Any, num_years: Any) -> float | None:
    """Return CAGR as a decimal using ``(end_val / start_val) ** (1 / years) - 1``.

    Both values and the number of years must be positive finite numbers. Returns
    ``None`` for missing, zero, negative, or non-finite inputs; equal valid
    values return ``0.0``.
    """
    start = _as_positive_finite_number(start_val)
    end = _as_positive_finite_number(end_val)
    years = _as_positive_finite_number(num_years)
    if start is None or end is None or years is None:
        return None
    if start == end:
        return 0.0
    return (end / start) ** (1 / years) - 1


def calculate_cagr_from_series(values: Sequence[Any], num_years: Any | None = None) -> float | None:
    """Calculate CAGR from ordered annual values using the first and last values.

    When ``num_years`` is omitted, the function treats adjacent annual values as
    one year apart, so a series of N observations spans N - 1 years. An explicit
    span is useful when historical observations are not annual or have gaps.
    """
    if values is None or len(values) < 2:
        return None
    years = len(values) - 1 if num_years is None else num_years
    return calculate_cagr(values[0], values[-1], years)
