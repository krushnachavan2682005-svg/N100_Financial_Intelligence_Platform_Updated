"""Cash-flow KPI calculations for financial-quality analysis."""

from __future__ import annotations

import math
from numbers import Real
from typing import Any


def _as_finite_number(value: Any) -> float | None:
    """Convert a usable numeric value to float, returning ``None`` when absent."""
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


def free_cash_flow(cash_from_operations: Any, capex: Any) -> float | None:
    """Calculate FCF: operating cash flow less capital expenditure.

    FCF measures cash remaining after investment required to maintain or expand
    the business. ``capex`` may be supplied as a positive expenditure or as a
    negative cash outflow from a cash-flow statement; its magnitude is deducted.
    Supply only the Capex component, not total investing cash flow, when other
    investing activities such as acquisitions or asset sales are present.
    """
    cfo = _as_finite_number(cash_from_operations)
    capex_value = _as_finite_number(capex)
    if cfo is None or capex_value is None:
        return None
    return cfo - abs(capex_value)


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
    """Return a finite ratio when both inputs are available and the base is non-zero."""
    numerator_value = _as_finite_number(numerator)
    denominator_value = _as_finite_number(denominator)
    if numerator_value is None or denominator_value is None or denominator_value == 0:
        return None
    return numerator_value / denominator_value


def fcf_to_net_profit(free_cash_flow_value: Any, net_profit: Any) -> float | None:
    """Calculate FCF-to-net-profit: cash conversion of accounting profit (FCF / net profit)."""
    return _safe_ratio(free_cash_flow_value, net_profit)


def cfo_to_ebitda(cash_from_operations: Any, ebitda: Any) -> float | None:
    """Calculate CFO-to-EBITDA: operating cash generated per unit of EBITDA."""
    return _safe_ratio(cash_from_operations, ebitda)


def cfo_to_operating_profit(cash_from_operations: Any, operating_profit: Any) -> float | None:
    """Calculate CFO-to-operating-profit: operating cash generated per unit of EBIT-like profit."""
    return _safe_ratio(cash_from_operations, operating_profit)
