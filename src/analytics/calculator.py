"""Calculate and transactionally load annual financial ratios into SQLite."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analytics.cagr import calculate_cagr_with_flag
from src.analytics.cashflow_kpis import (
    cfo_to_operating_profit,
    fcf_to_net_profit,
    free_cash_flow,
    write_capital_allocation_csv,
)
from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    interest_coverage,
    net_profit_margin,
    return_on_capital_employed,
    return_on_equity,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
OUTPUT_DIR = PROJECT_ROOT / "output"
RATIO_EDGE_CASES_LOG = OUTPUT_DIR / "ratio_edge_cases.log"
CAPITAL_ALLOCATION_CSV = OUTPUT_DIR / "capital_allocation.csv"

HIGH_LEVERAGE_THRESHOLD = 2.0
RATIO_DIFF_THRESHOLD_PCT = 5.0
FINANCIAL_SECTOR_KEYWORDS = ("bank", "finance", "nbfc")

logger = logging.getLogger(__name__)

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
    "sales_cagr_3y_flag",
    "sales_cagr_5y_flag",
    "free_cash_flow",
    "fcf_to_net_profit",
    "cfo_to_operating_profit",
    "source_name",
)

_RATIO_MIGRATIONS = {
    "sales_cagr_3y": "REAL",
    "sales_cagr_5y": "REAL",
    "sales_cagr_3y_flag": "TEXT",
    "sales_cagr_5y_flag": "TEXT",
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


def _is_financial_sector(sector: str | None) -> bool:
    """Return True for banks, NBFCs, and other financial-sector carve-outs."""
    if not sector:
        return False
    normalized = sector.casefold()
    return any(keyword in normalized for keyword in FINANCIAL_SECTOR_KEYWORDS)


def _ratio_difference_pct(computed: Any, source: Any) -> float | None:
    """Return absolute percentage-point difference between computed and source ratios."""
    if computed is None or source is None:
        return None
    return abs(float(computed) - float(source))


def _append_ratio_edge_case(
    edge_cases: list[str],
    *,
    company_id: str,
    year: int,
    metric: str,
    computed: float,
    source_value: float,
    source_column: str,
) -> None:
    diff = _ratio_difference_pct(computed, source_value)
    if diff is None or diff <= RATIO_DIFF_THRESHOLD_PCT:
        return
    edge_cases.append(
        f"{company_id},{year},{metric},{computed:.4f},{source_value:.4f},"
        f"{source_column},{diff:.4f}"
    )


def _maybe_warn_high_leverage(
    *,
    company_id: str,
    year: int,
    sector: str | None,
    debt_to_equity_value: float | None,
) -> None:
    """Log high-leverage warnings, suppressing the alert for financial-sector firms."""
    if debt_to_equity_value is None or debt_to_equity_value <= HIGH_LEVERAGE_THRESHOLD:
        return
    if _is_financial_sector(sector):
        logger.debug(
            "Suppressed high-leverage warning for financial-sector company %s (%s) in %s: D/E=%.2f",
            company_id,
            sector,
            year,
            debt_to_equity_value,
        )
        return
    logger.warning(
        "High leverage detected for %s in %s: D/E=%.2f exceeds %.2f",
        company_id,
        year,
        debt_to_equity_value,
        HIGH_LEVERAGE_THRESHOLD,
    )


def calculate_financial_ratio_records(
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Return one calculated financial-ratios record for every complete company-year.

    The surrogate balance sheet does not expose current assets/liabilities, so
    ``current_ratio`` is left ``None``. Operating profit is used as the available
    EBIT proxy, and investing cash flow is a Capex proxy for the surrogate data.
    """
    rows = connection.execute("""
        SELECT p.company_id, p.year, p.sales, p.operating_profit, p.interest,
               p.net_profit, p.eps,
               b.equity_capital, b.reserves, b.borrowings, b.other_liabilities,
               b.total_assets, cf.cash_from_operating_activity,
               cf.cash_from_investing_activity,
               c.sector, c.source_roe_pct, c.source_roce_pct,
               sr.roe_pct, sr.roce_pct
        FROM profitandloss AS p
        JOIN balancesheet AS b ON b.company_id = p.company_id AND b.year = p.year
        JOIN cashflow AS cf ON cf.company_id = p.company_id AND cf.year = p.year
        JOIN companies AS c ON c.company_id = p.company_id
        LEFT JOIN source_ratios AS sr
            ON sr.company_id = p.company_id AND sr.year = p.year
        ORDER BY p.company_id, p.year
        """).fetchall()

    sales_history: dict[str, dict[int, Any]] = {}
    for row in rows:
        sales_history.setdefault(row[0], {})[row[1]] = row[2]

    records: list[dict[str, Any]] = []
    for row in rows:
        (
            company_id,
            year,
            sales,
            operating_profit,
            interest,
            net_profit,
            eps,
            equity_capital,
            reserves,
            borrowings,
            other_liabilities,
            total_assets,
            cfo,
            investing_cash_flow,
            sector,
            source_roe_pct,
            source_roce_pct,
            source_ratio_roe,
            source_ratio_roce,
        ) = row
        net_worth = _net_worth(equity_capital, reserves)
        capital_employed = _capital_employed(total_assets, other_liabilities)
        fcf = free_cash_flow(cfo, investing_cash_flow)
        company_sales = sales_history[company_id]
        debt_to_equity_value = debt_to_equity(borrowings, net_worth)
        return_on_equity_pct = return_on_equity(net_profit, net_worth)
        return_on_capital_employed_pct = return_on_capital_employed(
            operating_profit, capital_employed
        )
        sales_cagr_3y, sales_cagr_3y_flag = calculate_cagr_with_flag(
            company_sales.get(year - 3), sales, 3
        )
        sales_cagr_5y, sales_cagr_5y_flag = calculate_cagr_with_flag(
            company_sales.get(year - 5), sales, 5
        )

        _maybe_warn_high_leverage(
            company_id=company_id,
            year=year,
            sector=sector,
            debt_to_equity_value=debt_to_equity_value,
        )

        records.append(
            {
                "company_id": company_id,
                "year": year,
                "current_ratio": None,
                "debt_to_equity": debt_to_equity_value,
                "interest_coverage": interest_coverage(operating_profit, interest),
                "gross_margin_pct": None,
                "net_margin_pct": net_profit_margin(net_profit, sales),
                "return_on_assets_pct": return_on_equity(net_profit, total_assets),
                "return_on_equity_pct": return_on_equity_pct,
                "return_on_capital_employed_pct": return_on_capital_employed_pct,
                "asset_turnover": asset_turnover(sales, total_assets),
                "earnings_per_share": eps,
                "price_to_earnings": None,
                "price_to_book": None,
                "dividend_yield_pct": None,
                "sales_cagr_3y": sales_cagr_3y,
                "sales_cagr_5y": sales_cagr_5y,
                "sales_cagr_3y_flag": sales_cagr_3y_flag,
                "sales_cagr_5y_flag": sales_cagr_5y_flag,
                "free_cash_flow": fcf,
                "fcf_to_net_profit": fcf_to_net_profit(fcf, net_profit),
                "cfo_to_operating_profit": cfo_to_operating_profit(
                    cfo, operating_profit
                ),
                "source_name": "calculated_from_financial_statements",
                "_audit_context": {
                    "source_ratio_roe": source_ratio_roe,
                    "source_ratio_roce": source_ratio_roce,
                    "source_roe_pct": source_roe_pct,
                    "source_roce_pct": source_roce_pct,
                },
            }
        )
    return records


def write_ratio_edge_cases_log(
    records: list[dict[str, Any]],
    output_path: str | Path = RATIO_EDGE_CASES_LOG,
) -> int:
    """Cross-check ROE/ROCE against source columns and write anomalies to a log file."""
    edge_cases: list[str] = []
    for record in records:
        audit_context = record.pop("_audit_context", {})
        company_id = record["company_id"]
        year = record["year"]
        computed_roe = record["return_on_equity_pct"]
        computed_roce = record["return_on_capital_employed_pct"]

        comparisons = (
            (
                "ROE",
                computed_roe,
                ("source_ratios.roe_pct", audit_context.get("source_ratio_roe")),
            ),
            (
                "ROE",
                computed_roe,
                ("companies.source_roe_pct", audit_context.get("source_roe_pct")),
            ),
            (
                "ROCE",
                computed_roce,
                ("source_ratios.roce_pct", audit_context.get("source_ratio_roce")),
            ),
            (
                "ROCE",
                computed_roce,
                ("companies.source_roce_pct", audit_context.get("source_roce_pct")),
            ),
        )
        for metric, computed_value, (source_column, source_value) in comparisons:
            if computed_value is None or source_value is None:
                continue
            _append_ratio_edge_case(
                edge_cases,
                company_id=company_id,
                year=year,
                metric=metric,
                computed=computed_value,
                source_value=source_value,
                source_column=source_column,
            )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with output_file.open("w", encoding="utf-8") as handle:
        handle.write("# Ratio edge-case audit log\n")
        handle.write(f"# generated_at={timestamp}\n")
        handle.write("# threshold_pct=5.0\n")
        handle.write("company_id,year,metric,computed,source,source_column,diff_pct\n")
        for line in edge_cases:
            handle.write(f"{line}\n")
    return len(edge_cases)


def run_screener_verification(
    connection: sqlite3.Connection,
    *,
    min_roe_pct: float = 15.0,
    max_debt_to_equity: float = 1.0,
) -> dict[str, Any]:
    """Verify companies meeting ROE and debt-to-equity screener thresholds."""
    rows = connection.execute(
        """
        SELECT fr.company_id, c.company_name, c.sector, fr.year,
               fr.return_on_equity_pct, fr.debt_to_equity
        FROM financial_ratios AS fr
        JOIN companies AS c ON c.company_id = fr.company_id
        WHERE fr.return_on_equity_pct > ?
          AND fr.debt_to_equity < ?
        ORDER BY fr.year DESC, fr.return_on_equity_pct DESC
        """,
        (min_roe_pct, max_debt_to_equity),
    ).fetchall()
    latest_year = connection.execute(
        "SELECT MAX(year) FROM financial_ratios"
    ).fetchone()[0]
    latest_matches = [row for row in rows if row[3] == latest_year]
    return {
        "min_roe_pct": min_roe_pct,
        "max_debt_to_equity": max_debt_to_equity,
        "total_matches": len(rows),
        "latest_year": latest_year,
        "latest_year_matches": len(latest_matches),
        "sample": latest_matches[:5],
    }


def _ensure_ratio_columns(connection: sqlite3.Connection) -> None:
    """Add Day-12 derived-metric columns when loading into an existing database."""
    present_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(financial_ratios)")
    }
    for column, data_type in _RATIO_MIGRATIONS.items():
        if column not in present_columns:
            connection.execute(
                f'ALTER TABLE financial_ratios ADD COLUMN "{column}" {data_type}'
            )


def load_financial_ratios(db_path: str | Path = "nifty100.db") -> int:
    """Calculate and upsert annual ratios into ``financial_ratios`` in one transaction."""
    # Ensure audit log directory and file always exist
    RATIO_EDGE_CASES_LOG.parent.mkdir(parents=True, exist_ok=True)
    RATIO_EDGE_CASES_LOG.touch(exist_ok=True)

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
            connection.executemany(
                statement,
                [
                    tuple(record[column] for column in RATIO_COLUMNS)
                    for record in records
                ],
            )

        write_ratio_edge_cases_log(records)
        write_capital_allocation_csv(connection, CAPITAL_ALLOCATION_CSV)
        screener = run_screener_verification(connection)
        logger.info(
            "Screener verification: %s total matches (ROE > %.1f%%, D/E < %.1f); "
            "%s matches in latest year %s",
            screener["total_matches"],
            screener["min_roe_pct"],
            screener["max_debt_to_equity"],
            screener["latest_year_matches"],
            screener["latest_year"],
        )
        return len(records)
    finally:
        connection.close()
