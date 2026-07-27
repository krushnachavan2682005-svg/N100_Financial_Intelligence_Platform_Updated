"""Core profitability and efficiency ratio calculations."""

from __future__ import annotations

import math
from numbers import Real
from typing import Any


def _as_finite_number(value: Any) -> float | None:
    """Convert a numeric input to a finite float, returning ``None`` when absent."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Real):
        number = float(value)
    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
    return number if math.isfinite(number) else None


def _safe_ratio(numerator: Any, denominator: Any, *, percentage: bool) -> float | None:
    """Return a ratio only when both values are finite and the denominator is non-zero."""
    numerator_value = _as_finite_number(numerator)
    denominator_value = _as_finite_number(denominator)
    if numerator_value is None or denominator_value is None or denominator_value == 0:
        return None

    ratio = numerator_value / denominator_value
    return ratio * 100 if percentage else ratio


def operating_profit_margin(operating_profit: Any, sales: Any) -> float | None:
    """Calculate OPM %: operating profit divided by sales, multiplied by 100."""
    return _safe_ratio(operating_profit, sales, percentage=True)


def net_profit_margin(net_profit: Any, sales: Any) -> float | None:
    """Calculate NPM %: net profit divided by sales, multiplied by 100."""
    return _safe_ratio(net_profit, sales, percentage=True)


def return_on_equity(net_profit: Any, net_worth: Any) -> float | None:
    """Calculate ROE %: net profit divided by shareholder net worth, multiplied by 100."""
    return _safe_ratio(net_profit, net_worth, percentage=True)


def return_on_capital_employed(ebit: Any, capital_employed: Any) -> float | None:
    """Calculate ROCE %: EBIT divided by capital employed, multiplied by 100."""
    return _safe_ratio(ebit, capital_employed, percentage=True)


def asset_turnover(sales: Any, total_assets: Any) -> float | None:
    """Calculate asset turnover: sales divided by total assets (times, not percent)."""
    return _safe_ratio(sales, total_assets, percentage=False)


# Concise aliases support analytics notebooks while retaining descriptive APIs.
calculate_opm = operating_profit_margin
calculate_npm = net_profit_margin
calculate_roe = return_on_equity
calculate_roce = return_on_capital_employed
calculate_asset_turnover = asset_turnover
