import os
import sqlite3
import pytest
from src.analytics.radar import generate_all_radar_charts

@pytest.fixture
def setup_db(tmp_path):
    conn = sqlite3.connect(":memory:")
    
    # Create tables
    conn.executescript("""
        CREATE TABLE companies (company_id TEXT PRIMARY KEY);
        CREATE TABLE profitandloss (company_id TEXT, year INTEGER, net_profit REAL, eps REAL);
        CREATE TABLE financial_ratios (
            company_id TEXT,
            year INTEGER,
            return_on_equity_pct REAL,
            return_on_capital_employed_pct REAL,
            net_margin_pct REAL,
            debt_to_equity REAL,
            free_cash_flow REAL,
            sales_cagr_5y REAL,
            interest_coverage REAL,
            asset_turnover REAL
        );
        CREATE TABLE peer_percentiles (
            company_id TEXT,
            peer_group_name TEXT,
            metric TEXT,
            percentile_rank REAL,
            year INTEGER
        );
    """)
    
    # Insert data
    conn.execute("INSERT INTO companies (company_id) VALUES ('TCS'), ('NTPC')")
    
    # TCS is in a peer group
    metrics = ["ROE", "ROCE", "Net Profit Margin", "D/E", "FCF", "PAT CAGR 5yr", "Revenue CAGR 5yr"]
    for m in metrics:
        conn.execute(
            "INSERT INTO peer_percentiles (company_id, peer_group_name, metric, percentile_rank, year) VALUES (?, ?, ?, ?, ?)",
            ("TCS", "IT Services", m, 0.8, 2023)
        )
        
    # NTPC is not in a peer group, so Nifty 100 fallback will trigger
    conn.execute(
        """INSERT INTO financial_ratios 
        (company_id, year, return_on_equity_pct, return_on_capital_employed_pct, net_margin_pct, 
         debt_to_equity, free_cash_flow, sales_cagr_5y, interest_coverage, asset_turnover) 
        VALUES ('NTPC', 2023, 15.0, 12.0, 10.0, 1.2, 500.0, 8.0, 4.0, 0.5)"""
    )
    
    yield conn
    conn.close()

def test_generate_all_radar_charts(setup_db, tmp_path):
    conn = setup_db
    out_dir = tmp_path / "radar_charts"
    
    generate_all_radar_charts(conn, str(out_dir))
    
    assert os.path.exists(out_dir)
    
    # Check that PNG files were created for TCS and NTPC
    tcs_file = out_dir / "TCS_radar.png"
    ntpc_file = out_dir / "NTPC_radar.png"
    
    assert tcs_file.exists()
    assert ntpc_file.exists()
    
    # Verify file sizes to ensure they are valid images
    assert tcs_file.stat().st_size > 0
    assert ntpc_file.stat().st_size > 0
