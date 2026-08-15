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
    cursor.execute(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (group_name,)
    )
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
            "labels": [
                "ROE",
                "ROCE",
                "OPM",
                "NPM",
                "Asset Turnover",
                "Debt to Equity",
                "Interest Coverage",
                "FCF Yield",
            ],
            "company_values": [15, 12, 20, 10, 1.2, 0.5, 8, 5],
            "peer_avg_values": [12, 10, 15, 8, 1.0, 0.8, 5, 4],
            "benchmark_values": [18, 15, 25, 15, 1.5, 0.2, 10, 8],
        },
    }
