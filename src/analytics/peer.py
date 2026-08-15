"""Peer group percentile rankings engine."""

import logging
import sqlite3
from typing import Dict, List, Tuple

from src.analytics.cagr import calculate_cagr_with_flag

logger = logging.getLogger(__name__)

METRICS = [
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "D/E",
    "FCF",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "EPS CAGR 5yr",
    "Interest Coverage",
    "Asset Turnover",
]


def _calc_percent_rank(
    values_with_ids: List[Tuple[str, float]], invert: bool = False
) -> Dict[str, float]:
    """Calculate PERCENT_RANK for a list of (company_id, value).

    Ties receive the lowest rank of the tied group.
    Returns a dict mapping company_id to its percentile rank.
    """
    if not values_with_ids:
        return {}
    if len(values_with_ids) == 1:
        # A single value gets rank 0.0, or 1.0 if inverted?
        # Standard PERCENT_RANK for 1 item is 0.0.
        # If invert, 1.0 - 0.0 = 1.0.
        return {values_with_ids[0][0]: 1.0 if invert else 0.0}

    sorted_items = sorted(values_with_ids, key=lambda x: x[1])
    n = len(sorted_items)
    ranks = {}
    current_rank = 1

    for i in range(n):
        if i > 0 and sorted_items[i][1] == sorted_items[i - 1][1]:
            # Tie: keep current_rank
            pass
        else:
            current_rank = i + 1

        pr = (current_rank - 1) / (n - 1)
        if invert:
            pr = 1.0 - pr

        ranks[sorted_items[i][0]] = pr

    return ranks


def create_peer_percentiles_table(connection: sqlite3.Connection) -> None:
    """Create the peer_percentiles table if it doesn't exist."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER NOT NULL,
            PRIMARY KEY (company_id, peer_group_name, metric, year),
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)


def calculate_peer_percentiles(connection: sqlite3.Connection) -> None:
    """Compute and store PERCENT_RANK across metrics for peer groups."""
    create_peer_percentiles_table(connection)

    # 1. Fetch PL history for CAGR calculation
    pl_rows = connection.execute(
        "SELECT company_id, year, net_profit, eps FROM profitandloss"
    ).fetchall()

    pl_history: Dict[str, Dict[int, Dict[str, float]]] = {}
    for cid, year, net_profit, eps in pl_rows:
        if cid not in pl_history:
            pl_history[cid] = {}
        pl_history[cid][year] = {"net_profit": net_profit, "eps": eps}

    # 2. Fetch financial ratios and peer group info
    fr_rows = connection.execute("""
        SELECT 
            fr.company_id,
            fr.year,
            pg.peer_group_name,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.net_margin_pct,
            fr.debt_to_equity,
            fr.free_cash_flow,
            fr.sales_cagr_5y,
            fr.interest_coverage,
            fr.asset_turnover
        FROM financial_ratios fr
        LEFT JOIN peer_groups pg ON fr.company_id = pg.company_id
    """).fetchall()

    # Group data: peer_group_name -> year -> metric -> list of (company_id, value)
    data: Dict[str, Dict[int, Dict[str, List[Tuple[str, float]]]]] = {}

    for row in fr_rows:
        cid, year, pg_name, roe, roce, npm, de, fcf, rev_cagr, ic, at = row

        if not pg_name:
            logger.info("No peer group assigned for company %s", cid)
            continue

        if pg_name not in data:
            data[pg_name] = {}
        if year not in data[pg_name]:
            data[pg_name][year] = {m: [] for m in METRICS}

        metrics_vals = {
            "ROE": roe,
            "ROCE": roce,
            "Net Profit Margin": npm,
            "D/E": de,
            "FCF": fcf,
            "Revenue CAGR 5yr": rev_cagr,
            "Interest Coverage": ic,
            "Asset Turnover": at,
        }

        # Calculate PAT CAGR 5yr
        pat_cagr = None
        if (
            cid in pl_history
            and year in pl_history[cid]
            and (year - 5) in pl_history[cid]
        ):
            start_val = pl_history[cid][year - 5]["net_profit"]
            end_val = pl_history[cid][year]["net_profit"]
            pat_cagr, _ = calculate_cagr_with_flag(start_val, end_val, 5)
        metrics_vals["PAT CAGR 5yr"] = pat_cagr

        # Calculate EPS CAGR 5yr
        eps_cagr = None
        if (
            cid in pl_history
            and year in pl_history[cid]
            and (year - 5) in pl_history[cid]
        ):
            start_val = pl_history[cid][year - 5]["eps"]
            end_val = pl_history[cid][year]["eps"]
            eps_cagr, _ = calculate_cagr_with_flag(start_val, end_val, 5)
        metrics_vals["EPS CAGR 5yr"] = eps_cagr

        for m, v in metrics_vals.items():
            if v is not None:
                data[pg_name][year][m].append((cid, float(v)))

    # 3. Calculate ranks and prepare insertion records
    records = []
    for pg_name, years_data in data.items():
        for year, metrics_data in years_data.items():
            for m, values_with_ids in metrics_data.items():
                ranks = _calc_percent_rank(values_with_ids, invert=(m == "D/E"))

                # We need to map back to the original values to save them
                val_dict = dict(values_with_ids)

                for cid, pr in ranks.items():
                    records.append((cid, pg_name, m, val_dict[cid], pr, year))

    # 4. Insert into database
    if records:
        with connection:
            connection.executemany(
                """
                INSERT INTO peer_percentiles (
                    company_id, peer_group_name, metric, value, percentile_rank, year
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_id, peer_group_name, metric, year) DO UPDATE SET
                    value=excluded.value,
                    percentile_rank=excluded.percentile_rank
            """,
                records,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_path = "nifty100.db"
    conn = sqlite3.connect(db_path)
    try:
        calculate_peer_percentiles(conn)
        print("Peer percentiles calculated successfully.")
    finally:
        conn.close()
