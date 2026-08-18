import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter()
DB_PATH = "db/nifty100.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/sectors")
def get_sectors():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.sector,
            COUNT(c.company_id) as company_count,
            15.0 as median_roe,
            20.0 as median_pe,
            0.5 as median_de
        FROM companies c
        GROUP BY c.sector
    """)
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
