import time
import sqlite3
from fastapi import APIRouter

router = APIRouter()
START_TIME = time.time()

# Hardcoding standard tables to check row counts
TABLES_TO_CHECK = [
    'companies',
    'profitandloss',
    'balancesheet',
    'cashflow',
    'financial_ratios',
    'peer_percentiles'
]

@router.get("/health")
def health_check():
    uptime_seconds = time.time() - START_TIME
    
    db_row_counts = {}
    try:
        conn = sqlite3.connect('nifty100.db', check_same_thread=False)
        cursor = conn.cursor()
        
        for table in TABLES_TO_CHECK:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                db_row_counts[table] = count
            except sqlite3.OperationalError:
                db_row_counts[table] = "Error: Table not found or unreadable"
        conn.close()
    except Exception as e:
        db_row_counts["db_connection"] = f"Failed to connect: {str(e)}"
        
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "db_row_counts": db_row_counts
    }
