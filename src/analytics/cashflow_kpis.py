"""Cash-flow KPI calculations for financial-quality analysis."""

from __future__ import annotations

import csv
import math
import sqlite3
from numbers import Real
from pathlib import Path
from typing import Any


CAPITAL_ALLOCATION_PATTERNS: dict[tuple[str, str, str], str] = {
    ("+", "+", "-"): "Debt Repayer",
    ("+", "-", "-"): "Reinvestor",
    ("+", "-", "+"): "Growth Financier",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Startup Financier",
    ("-", "+", "-"): "Restructuring",
    ("-", "-", "-"): "Cash Burn",
    ("+", "+", "+"): "Cash Accumulator",
}


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


def cash_flow_sign(value: Any) -> str | None:
    """Return ``+``, ``-``, or ``0`` for a cash-flow component."""
    number = _as_finite_number(value)
    if number is None:
        return None
    if number > 0:
        return "+"
    if number < 0:
        return "-"
    return "0"


def classify_capital_allocation(
    cash_from_operations: Any,
    cash_from_investing: Any,
    cash_from_financing: Any,
) -> dict[str, Any]:
    """Classify the eight-pattern capital allocation label from CFO/CFI/CFF signs."""
    cfo_sign = cash_flow_sign(cash_from_operations)
    cfi_sign = cash_flow_sign(cash_from_investing)
    cff_sign = cash_flow_sign(cash_from_financing)
    if None in {cfo_sign, cfi_sign, cff_sign}:
        pattern_label = "Incomplete"
    elif "0" in {cfo_sign, cfi_sign, cff_sign}:
        pattern_label = "Neutral Flow"
    else:
        pattern_label = CAPITAL_ALLOCATION_PATTERNS.get(
            (cfo_sign, cfi_sign, cff_sign), "Unknown"
        )
    return {
        "cfo_sign": cfo_sign,
        "cfi_sign": cfi_sign,
        "cff_sign": cff_sign,
        "pattern_label": pattern_label,
    }


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


def build_capital_allocation_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return capital-allocation classifier rows for every complete cash-flow record."""
    rows = connection.execute(
        """
        SELECT company_id, year,
               cash_from_operating_activity,
               cash_from_investing_activity,
               cash_from_financing_activity
        FROM cashflow
        ORDER BY company_id, year
        """
    ).fetchall()
    records: list[dict[str, Any]] = []
    for company_id, year, cfo, cfi, cff in rows:
        classification = classify_capital_allocation(cfo, cfi, cff)
        records.append(
            {
                "company_id": company_id,
                "year": year,
                **classification,
            }
        )
    return records


def write_capital_allocation_csv(
    connection: sqlite3.Connection,
    output_path: str | Path,
) -> int:
    """Write the capital-allocation audit CSV and return the number of rows written."""
    records = build_capital_allocation_records(connection)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label")
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    return len(records)
