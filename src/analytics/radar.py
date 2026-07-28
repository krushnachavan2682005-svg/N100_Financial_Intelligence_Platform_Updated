"""Generate polar/radar chart images for all companies."""

import logging
import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np

from src.analytics.peer import _calc_percent_rank, METRICS

logger = logging.getLogger(__name__)

def _get_nifty100_percentiles(connection: sqlite3.Connection) -> Dict[str, Dict[str, float]]:
    """Calculate percentiles across all Nifty 100 companies for the latest year."""
    # We need to fetch the raw values just like in peer.py but without grouping by peer group
    
    pl_rows = connection.execute(
        "SELECT company_id, year, net_profit, eps FROM profitandloss"
    ).fetchall()
    
    pl_history: Dict[str, Dict[int, Dict[str, float]]] = {}
    for cid, year, net_profit, eps in pl_rows:
        if cid not in pl_history:
            pl_history[cid] = {}
        pl_history[cid][year] = {"net_profit": net_profit, "eps": eps}
        
    fr_rows = connection.execute("""
        SELECT 
            company_id,
            year,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            net_margin_pct,
            debt_to_equity,
            free_cash_flow,
            sales_cagr_5y,
            interest_coverage,
            asset_turnover
        FROM financial_ratios
    """).fetchall()
    
    # We only care about the latest year for radar charts
    if not fr_rows:
        return {}
    
    latest_year = max(r[1] for r in fr_rows)
    
    metrics_data = {m: [] for m in METRICS}
    
    for row in fr_rows:
        (
            cid, year, roe, roce, npm, de, fcf, rev_cagr, ic, at
        ) = row
        
        if year != latest_year:
            continue
            
        from src.analytics.cagr import calculate_cagr_with_flag
        
        # PAT CAGR
        pat_cagr = None
        if cid in pl_history and year in pl_history[cid] and (year - 5) in pl_history[cid]:
            start_val = pl_history[cid][year - 5]["net_profit"]
            end_val = pl_history[cid][year]["net_profit"]
            pat_cagr, _ = calculate_cagr_with_flag(start_val, end_val, 5)
            
        # EPS CAGR
        eps_cagr = None
        if cid in pl_history and year in pl_history[cid] and (year - 5) in pl_history[cid]:
            start_val = pl_history[cid][year - 5]["eps"]
            end_val = pl_history[cid][year]["eps"]
            eps_cagr, _ = calculate_cagr_with_flag(start_val, end_val, 5)
            
        vals = {
            "ROE": roe,
            "ROCE": roce,
            "Net Profit Margin": npm,
            "D/E": de,
            "FCF": fcf,
            "Revenue CAGR 5yr": rev_cagr,
            "EPS CAGR 5yr": eps_cagr,
            "PAT CAGR 5yr": pat_cagr,
            "Interest Coverage": ic,
            "Asset Turnover": at,
        }
        
        for m, v in vals.items():
            if v is not None:
                metrics_data[m].append((cid, float(v)))
                
    result = {}
    for m, values_with_ids in metrics_data.items():
        ranks = _calc_percent_rank(values_with_ids, invert=(m == "D/E"))
        for cid, pr in ranks.items():
            if cid not in result:
                result[cid] = {}
            result[cid][m] = pr
            
    return result

def plot_radar_chart(
    company_id: str, 
    metrics: List[str], 
    values: List[float], 
    baseline_label: str,
    output_dir: str
) -> None:
    """Generate and save a radar chart for a company."""
    # Ensure there are exactly 8 metrics as per requirement
    if len(metrics) != 8:
        logger.warning(f"Expected 8 metrics, got {len(metrics)}")
        
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    
    # Complete the loop
    values = values + [values[0]]
    angles = angles + [angles[0]]
    
    baseline = [0.5] * len(metrics) + [0.5]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Plot company
    ax.plot(angles, values, color='#1f77b4', linewidth=2, label=company_id)
    ax.fill(angles, values, color='#1f77b4', alpha=0.25)
    
    # Plot baseline
    ax.plot(angles, baseline, color='#ff7f0e', linewidth=2, linestyle='dashed', label=baseline_label)
    
    # Labels
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=10)
    
    # Set yticks to be bounded by [0, 1] for percentile rank
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25th', '50th', '75th', '100th'], color="grey", size=8)
    ax.set_ylim(0, 1)
    
    plt.title(f"{company_id} Performance Radar", size=14, color='black', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Save
    out_path = Path(output_dir) / f"{company_id}_radar.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def generate_all_radar_charts(connection: sqlite3.Connection, output_dir: str = "reports/radar_charts/") -> None:
    """Generate radar charts for all companies."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 8 axes to plot as per requirements
    axes_metrics = [
        "ROE",
        "ROCE",
        "Net Profit Margin",
        "D/E", # In code we'll label it D/E (percentile rank) but DB metric is D/E
        "FCF", # FCF score
        "PAT CAGR 5yr",
        "Revenue CAGR 5yr",
        "Composite Score"
    ]
    
    # 1. Fetch peer_percentiles for latest year
    try:
        latest_year = connection.execute("SELECT MAX(year) FROM peer_percentiles").fetchone()[0]
    except sqlite3.OperationalError:
        latest_year = None
        
    peer_data = {}
    if latest_year is not None:
        rows = connection.execute(
            "SELECT company_id, metric, percentile_rank FROM peer_percentiles WHERE year=?", 
            (latest_year,)
        ).fetchall()
        for cid, m, pr in rows:
            if cid not in peer_data:
                peer_data[cid] = {}
            peer_data[cid][m] = pr
            
    # 2. Get Nifty 100 percentiles as fallback
    nifty100_data = _get_nifty100_percentiles(connection)
    
    # All companies in DB
    companies = [r[0] for r in connection.execute("SELECT company_id FROM companies").fetchall()]
    
    count = 0
    for cid in companies:
        is_peer = cid in peer_data
        data_source = peer_data[cid] if is_peer else nifty100_data.get(cid, {})
        
        if not data_source:
            logger.info("No data available for company %s", cid)
            continue
            
        plot_values = []
        valid = True
        
        raw_7_metrics = []
        for m in axes_metrics[:-1]: # First 7 metrics
            val = data_source.get(m)
            if val is None:
                val = 0.0 # fallback if missing
            plot_values.append(val)
            raw_7_metrics.append(val)
            
        # Composite score
        composite = sum(raw_7_metrics) / len(raw_7_metrics) if raw_7_metrics else 0.0
        plot_values.append(composite)
        
        display_metrics = [
            "ROE", "ROCE", "Net Profit Margin", "D/E Rank",
            "FCF Score", "PAT CAGR 5yr", "Revenue CAGR 5yr", "Composite Score"
        ]
        
        baseline_label = "Peer Group Avg" if is_peer else "Nifty 100 Avg"
        
        plot_radar_chart(cid, display_metrics, plot_values, baseline_label, output_dir)
        count += 1
        
    logger.info(f"Successfully generated {count} radar charts in {output_dir}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_path = "nifty100.db"
    conn = sqlite3.connect(db_path)
    try:
        generate_all_radar_charts(conn)
    finally:
        conn.close()
