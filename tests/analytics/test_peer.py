import sqlite3
import pytest
from src.analytics.peer import _calc_percent_rank, calculate_peer_percentiles

def test_calc_percent_rank():
    # Test with standard behavior
    values = [
        ("C1", 10.0),
        ("C2", 20.0),
        ("C3", 20.0),
        ("C4", 30.0)
    ]
    # Sorted: C1 (10), C2 (20), C3 (20), C4 (30)
    # Ranks: C1 -> 1, C2 -> 2, C3 -> 2, C4 -> 4
    # Percent Ranks:
    # C1: (1-1)/3 = 0.0
    # C2: (2-1)/3 = 0.3333
    # C3: (2-1)/3 = 0.3333
    # C4: (4-1)/3 = 1.0
    ranks = _calc_percent_rank(values, invert=False)
    assert ranks["C1"] == 0.0
    assert abs(ranks["C2"] - 1/3) < 1e-5
    assert abs(ranks["C3"] - 1/3) < 1e-5
    assert ranks["C4"] == 1.0

def test_calc_percent_rank_invert_de():
    # Test inverse for D/E
    values = [
        ("C1", 0.1),
        ("C2", 0.5),
        ("C3", 1.0)
    ]
    # Pranks without invert: C1: 0.0, C2: 0.5, C3: 1.0
    # Inverted: C1: 1.0, C2: 0.5, C3: 0.0
    ranks = _calc_percent_rank(values, invert=True)
    assert ranks["C1"] == 1.0
    assert ranks["C2"] == 0.5
    assert ranks["C3"] == 0.0

@pytest.fixture
def setup_db():
    conn = sqlite3.connect(":memory:")
    
    # Create required tables
    conn.executescript("""
        CREATE TABLE companies (company_id TEXT PRIMARY KEY);
        CREATE TABLE profitandloss (company_id TEXT, year INTEGER, net_profit REAL, eps REAL);
        CREATE TABLE peer_groups (company_id TEXT, peer_group_name TEXT);
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
    """)
    
    # Insert dummy data
    # Companies
    conn.execute("INSERT INTO companies (company_id) VALUES ('TCS'), ('INFY'), ('HUL'), ('ITC')")
    
    # Peer groups (IT Services and FMCG)
    conn.execute("INSERT INTO peer_groups (company_id, peer_group_name) VALUES ('TCS', 'IT Services'), ('INFY', 'IT Services')")
    conn.execute("INSERT INTO peer_groups (company_id, peer_group_name) VALUES ('HUL', 'FMCG'), ('ITC', 'FMCG')")
    
    # Financial Ratios
    conn.execute("""
        INSERT INTO financial_ratios (
            company_id, year, return_on_equity_pct, debt_to_equity
        ) VALUES 
        ('TCS', 2023, 40.0, 0.0),
        ('INFY', 2023, 30.0, 0.1),
        ('HUL', 2023, 20.0, 0.2),
        ('ITC', 2023, 25.0, 0.0)
    """)
    
    # P&L for CAGR (year 2018 and 2023)
    conn.execute("""
        INSERT INTO profitandloss (company_id, year, net_profit, eps) VALUES
        ('TCS', 2018, 100, 10),
        ('TCS', 2023, 200, 20),
        ('INFY', 2018, 50, 5),
        ('INFY', 2023, 100, 10)
    """)
    
    yield conn
    conn.close()

def test_calculate_peer_percentiles(setup_db):
    conn = setup_db
    calculate_peer_percentiles(conn)
    
    # Check if table is created and populated
    cursor = conn.execute("SELECT company_id, peer_group_name, metric, value, percentile_rank FROM peer_percentiles")
    rows = cursor.fetchall()
    assert len(rows) > 0
    
    # Test IT Services ROE ranking
    tcs_roe = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='TCS' AND metric='ROE'").fetchone()[0]
    infy_roe = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='INFY' AND metric='ROE'").fetchone()[0]
    
    # TCS (40.0) should be > INFY (30.0)
    # INFY is 0.0 (lowest), TCS is 1.0 (highest)
    assert infy_roe == 0.0
    assert tcs_roe == 1.0
    
    # Test D/E ranking (Inverse)
    tcs_de = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='TCS' AND metric='D/E'").fetchone()[0]
    infy_de = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='INFY' AND metric='D/E'").fetchone()[0]
    
    # TCS D/E = 0.0, INFY D/E = 0.1
    # Lower D/E should have higher rank.
    assert tcs_de == 1.0
    assert infy_de == 0.0
    
    # Test FMCG group
    hul_roe = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='HUL' AND metric='ROE'").fetchone()[0]
    itc_roe = conn.execute("SELECT percentile_rank FROM peer_percentiles WHERE company_id='ITC' AND metric='ROE'").fetchone()[0]
    
    # HUL (20.0), ITC (25.0)
    assert hul_roe == 0.0
    assert itc_roe == 1.0
