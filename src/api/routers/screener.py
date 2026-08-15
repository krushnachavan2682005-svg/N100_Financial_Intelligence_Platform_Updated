import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException

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
    max_pe: Optional[float] = None,
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
