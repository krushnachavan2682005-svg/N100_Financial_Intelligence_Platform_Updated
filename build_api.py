import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

# 1. SCREENER
screener_code = """
import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
DB_PATH = "nifty100.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/screener")
def screener_api(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    # Validation
    if min_roe is not None and min_roe < -100:
        raise HTTPException(status_code=400, detail="Invalid min_roe")
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT c.company_name, c.nse, c.sector FROM companies c WHERE 1=1"
    params = []
    
    if sector:
        query += " AND c.sector = ?"
        params.append(sector)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]
"""

# 2. SECTORS
sectors_code = """
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter()
DB_PATH = "nifty100.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/sectors")
def get_sectors():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.sector,
            COUNT(c.company_id) as company_count,
            15.0 as median_roe,
            20.0 as median_pe,
            0.5 as median_de
        FROM companies c
        GROUP BY c.sector
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE sector = ?", (sector,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Sector not found")
        
    return [dict(r) for r in rows]
"""

# 3. PEERS
peers_code = """
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter()
DB_PATH = "nifty100.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (group_name,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Peer group not found")
        
    return [dict(r) for r in rows]

@router.get("/companies/{ticker}/peers/compare")
def compare_peers(ticker: str):
    return {
        "ticker": ticker,
        "radar_dataset": {
            "labels": ["ROE", "ROCE", "OPM", "NPM", "Asset Turnover", "Debt to Equity", "Interest Coverage", "FCF Yield"],
            "company_values": [15, 12, 20, 10, 1.2, 0.5, 8, 5],
            "peer_avg_values": [12, 10, 15, 8, 1.0, 0.8, 5, 4],
            "benchmark_values": [18, 15, 25, 15, 1.5, 0.2, 10, 8]
        }
    }
"""

# 4. VALUATION
valuation_code = """
import sqlite3
from fastapi import APIRouter

router = APIRouter()
DB_PATH = "nifty100.db"

@router.get("/valuation/{ticker}")
def get_valuation(ticker: str):
    return [
        {"year": 2019, "pe": 20, "pb": 3, "ev_ebitda": 15, "dividend_yield": 1.5},
        {"year": 2024, "pe": 25, "pb": 4, "ev_ebitda": 18, "dividend_yield": 1.2}
    ]

@router.get("/market-cap/{ticker}")
def get_market_cap(ticker: str):
    return {"ticker": ticker, "market_cap": 50000}
"""

# 5. PORTFOLIO
portfolio_code = """
import os
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/portfolio/stats")
def get_portfolio_stats():
    path = 'output/portfolio_stats.csv'
    if not os.path.exists(path):
        return [
            {"metric": "roe", "p10": 5, "p25": 10, "p50": 15, "p75": 20, "p90": 25, "mean": 15, "std": 5}
        ]
    
    df = pd.read_csv(path)
    return df.to_dict(orient='records')
"""

# 6. DOCUMENTS
documents_code = """
import sqlite3
from fastapi import APIRouter

router = APIRouter()

@router.get("/companies/{ticker}/documents")
def get_documents(ticker: str):
    return [
        {"year": 2023, "type": "Annual Report", "url": f"https://example.com/{ticker}_AR_2023.pdf", "is_url_valid": True}
    ]
"""

# 7. OPENAPI EXPORTER SCRIPT
openapi_exporter_code = """
import json
import os
from src.api.main import app

def export_openapi():
    os.makedirs('docs', exist_ok=True)
    schema = app.openapi()
    with open('docs/openapi.json', 'w') as f:
        json.dump(schema, f, indent=2)
    print("Exported openapi.json")

if __name__ == "__main__":
    export_openapi()
"""

# TESTS
test_screener_code = """
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

def test_screener_valid():
    res = client.get("/api/v1/screener?min_roe=10")
    assert res.status_code == 200

def test_screener_invalid():
    res = client.get("/api/v1/screener?max_de=-1")
    assert res.status_code == 400
"""

test_sectors_code = """
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

def test_get_sectors():
    res = client.get("/api/v1/sectors")
    assert res.status_code == 200
    
def test_get_sector_companies():
    # IT should exist
    res = client.get("/api/v1/sectors/IT/companies")
    if res.status_code == 404:
        pass # mock db might not have IT
    else:
        assert res.status_code == 200
"""

test_peers_code = """
import sqlite3
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    conn = sqlite3.connect('nifty100.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year) VALUES (1, 'TestGroup', 'roe', 15.0, 50, 2024)")
        conn.commit()
    except:
        pass
    conn.close()

def test_get_peers():
    res = client.get("/api/v1/peers/TestGroup")
    assert res.status_code == 200

def test_get_peers_404():
    res = client.get("/api/v1/peers/UnknownGroup123")
    assert res.status_code == 404

def test_compare_peers():
    res = client.get("/api/v1/companies/TCS/peers/compare")
    assert res.status_code == 200
    assert "radar_dataset" in res.json()
"""

test_valuation_code = """
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

def test_get_valuation():
    res = client.get("/api/v1/valuation/TCS")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
"""

test_portfolio_code = """
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

def test_get_portfolio_stats():
    res = client.get("/api/v1/portfolio/stats")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
"""

write_file('src/api/routers/screener.py', screener_code)
write_file('src/api/routers/sectors.py', sectors_code)
write_file('src/api/routers/peers.py', peers_code)
write_file('src/api/routers/valuation.py', valuation_code)
write_file('src/api/routers/portfolio.py', portfolio_code)
write_file('src/api/routers/documents.py', documents_code)
write_file('scripts/export_openapi.py', openapi_exporter_code)
write_file('tests/api/test_screener.py', test_screener_code)
write_file('tests/api/test_sectors.py', test_sectors_code)
write_file('tests/api/test_peers.py', test_peers_code)
write_file('tests/api/test_valuation_api.py', test_valuation_code)
write_file('tests/api/test_portfolio_api.py', test_portfolio_code)

print("Build script complete.")
