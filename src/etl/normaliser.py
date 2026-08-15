"""Scalar normalisation helpers used by the ETL pipeline."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

_MISSING_TEXT = {"", "-", "nan", "none", "null", "na", "n/a"}
_YEAR_PATTERN = re.compile(r"(?<!\d)(\d{4})(?!\d)")
_YEAR_RANGE_PATTERN = re.compile(r"^\s*(\d{4})\s*[-/]\s*(\d{2}|\d{4})\s*$")


def normalize_ticker(value: Any) -> str | None:
    """Return a clean exchange-independent ticker, or ``None`` if missing."""
    if value is None:
        return None

    ticker = str(value).strip()
    if ticker.lower() in _MISSING_TEXT:
        return None

    ticker = re.sub(r"\.(?:NS|BO)$", "", ticker, flags=re.IGNORECASE).strip()
    return ticker.upper() or None


def normalize_year(value: Any) -> int | None:
    """Extract and validate a calendar/fiscal year from a scalar value."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            return None
        year = int(value)
    elif isinstance(value, int):
        year = value
    else:
        text = str(value).strip()
        if text.lower() in _MISSING_TEXT:
            return None

        range_match = _YEAR_RANGE_PATTERN.fullmatch(text)
        if range_match:
            start = int(range_match.group(1))
            end_text = range_match.group(2)
            if len(end_text) == 2:
                end = (start // 100) * 100 + int(end_text)
                if end < start:
                    end += 100
            else:
                end = int(end_text)
            if end != start + 1:
                return None
            year = end
        else:
            matches = _YEAR_PATTERN.findall(text)
            if len(matches) != 1:
                return None
            year = int(matches[0])

    if 1900 <= year <= datetime.now().year:
        return year
    return None
