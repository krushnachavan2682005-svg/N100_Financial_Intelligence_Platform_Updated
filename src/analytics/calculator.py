"""Calculate and transactionally load annual financial ratios into SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    cfo_to_operating_profit,
    fcf_to_net_profit,
    free_cash_flow,
)
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"

RATIO_COLUMNS = (
    "company_id",
    "year",
    "current_ratio",
    "debt_to_equity",
    "interest_coverage",
    "gross_margin_pct",
    "net_margin_pct",
    "return_on_assets_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "asset_turnover",
    "earnings_per_share",
    "price_to_earnings",
    "price_to_book",
    "dividend_yield_pct",
    "sales_cagr_3y",
    "sales_cagr_5y",
    "free_cash_flow",
    "fcf_to_net_profit",
    "cfo_to_operating_profit",
    "source_name",
)

_RATIO_MIGRATIONS = {
    "sales_cagr_3y": "REAL",
    "sales_cagr_5y": "REAL",
    "free_cash_flow": "REAL",
    "fcf_to_net_profit": "REAL",
    "cfo_to_operating_profit": "REAL",
}


def _net_worth(equity_capital: Any, reserves: Any) -> float | None:
    """Return equity capital plus reserves, if both balance-sheet inputs exist."""
    if equity_capital is None or reserves is None:
        return None
    return float(equity_capital) + float(reserves)


def _capital_employed(total_assets: Any, other_liabilities: Any) -> float | None:
    """Approximate capital employed as total assets less other/current liabilities."""
    if total_assets is None or other_liabilities is None:
        return None
    return float(total_assets) - float(other_liabilities)


def calculate_financial_ratio_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return one calculated financial-ratios record for every complete company-year.

    The surrogate balance sheet does not expose current assets/liabilities, so
    ``current_ratio`` is left ``None``. Operating profit is used as the available
    EBIT proxy, and investing cash flow is a Capex proxy for the surrogate data.
    """
    rows = connection.execute(
        """
        SELECT p.company_id, p.year, p.sales, p.operating_profit, p.interest,
               p.net_profit, p.eps,
               b.equity_capital, b.reserves, b.borrowings, b.other_liabilities,
               b.total_assets, cf.cash_from_operating_activity,
               cf.cash_from_investing_activity
        FROM profitandloss AS p
        JOIN balancesheet AS b ON b.company_id = p.company_id AND b.year = p.year
        JOIN cashflow AS cf ON cf.company_id = p.company_id AND cf.year = p.year
        ORDER BY p.company_id, p.year
        """
    ).fetchall()

    sales_history: dict[str, dict[int, Any]] = {}
    for row in rows:
        sales_history.setdefault(row[0], {})[row[1]] = row[2]

    records: list[dict[str, Any]] = []
    for row in rows:
        (
            company_id, year, sales, operating_profit, interest, net_profit, eps,
            equity_capital, reserves, borrowings,
            other_liabilities, total_assets, cfo, investing_cash_flow,
        ) = row
        net_worth = _net_worth(equity_capital, reserves)
        capital_employed = _capital_employed(total_assets, other_liabilities)
        fcf = free_cash_flow(cfo, investing_cash_flow)
        company_sales = sales_history[company_id]

        records.append(
            {
                "company_id": company_id,
                "year": year,
                "current_ratio": None,
                "debt_to_equity": debt_to_equity(borrowings, net_worth),
                "interest_coverage": interest_coverage(operating_profit, interest),
                "gross_margin_pct": None,
                "net_margin_pct": net_profit_margin(net_profit, sales),
                "return_on_assets_pct": return_on_equity(net_profit, total_assets),
                "return_on_equity_pct": return_on_equity(net_profit, net_worth),
                "return_on_capital_employed_pct": return_on_capital_employed(
                    operating_profit, capital_employed
                ),
                "asset_turnover": asset_turnover(sales, total_assets),
                "earnings_per_share": eps,
                "price_to_earnings": None,
                "price_to_book": None,
                "dividend_yield_pct": None,
                "sales_cagr_3y": calculate_cagr(company_sales.get(year - 3), sales, 3),
                "sales_cagr_5y": calculate_cagr(company_sales.get(year - 5), sales, 5),
                "free_cash_flow": fcf,
                "fcf_to_net_profit": fcf_to_net_profit(fcf, net_profit),
                "cfo_to_operating_profit": cfo_to_operating_profit(cfo, operating_profit),
                "source_name": "calculated_from_financial_statements",
            }
        )
    return records


def _ensure_ratio_columns(connection: sqlite3.Connection) -> None:
    """Add Day-12 derived-metric columns when loading into an existing database."""
    present_columns = {row[1] for row in connection.execute("PRAGMA table_info(financial_ratios)")}
    for column, data_type in _RATIO_MIGRATIONS.items():
        if column not in present_columns:
            connection.execute(f'ALTER TABLE financial_ratios ADD COLUMN "{column}" {data_type}')


def load_financial_ratios(db_path: str | Path = "nifty100.db") -> int:
    """Calculate and upsert annual ratios into ``financial_ratios`` in one transaction."""
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        with connection:
            _ensure_ratio_columns(connection)
            records = calculate_financial_ratio_records(connection)
            if not records:
                return 0

            quoted_columns = ", ".join(f'"{column}"' for column in RATIO_COLUMNS)
            placeholders = ", ".join("?" for _ in RATIO_COLUMNS)
            updates = ", ".join(
                f'"{column}" = excluded."{column}"'
                for column in RATIO_COLUMNS
                if column not in {"company_id", "year"}
            )
            statement = (
                f"INSERT INTO financial_ratios ({quoted_columns}) VALUES ({placeholders}) "
                f"ON CONFLICT (company_id, year) DO UPDATE SET {updates}"
            )
            connection.executemany(statement, [tuple(record[column] for column in RATIO_COLUMNS) for record in records])
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key integrity check failed: {violations}")
        return len(records)
    finally:
        connection.close()


if __name__ == "__main__":
    rows_loaded = load_financial_ratios(PROJECT_ROOT / "nifty100.db")
    print(f"Loaded or updated {rows_loaded} financial_ratios records.")
