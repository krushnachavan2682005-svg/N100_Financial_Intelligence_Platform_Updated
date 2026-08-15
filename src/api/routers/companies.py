import sqlite3
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
DB_PATH = "nifty100.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/companies")
def get_companies(
    sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            company_id as id, 
            company_name, 
            sector as broad_sector,
            '' as sub_sector,
            market_cap_cr as market_cap_crore,
            source_roe_pct as roe_pct,
            source_roce_pct as roce_pct,
            nse
        FROM companies
        WHERE 1=1
    """
    params = []

    if sector:
        query += " AND sector = ?"
        params.append(sector)

    if market_cap_category:
        # A simple mocked logic for market cap category filtering
        if market_cap_category.lower() == "large cap":
            query += " AND market_cap_cr >= 20000"
        elif market_cap_category.lower() == "mid cap":
            query += " AND market_cap_cr >= 5000 AND market_cap_cr < 20000"
        elif market_cap_category.lower() == "small cap":
            query += " AND market_cap_cr < 5000"

    if search:
        query += " AND (company_name LIKE ? OR nse LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get basic profile
    cursor.execute("SELECT * FROM companies WHERE nse = ?", (ticker,))
    company = cursor.fetchone()

    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company ticker not found")

    company_dict = dict(company)

    # Get latest financial ratios
    cursor.execute(
        """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC 
        LIMIT 1
    """,
        (company_dict["company_id"],),
    )
    ratios = cursor.fetchone()

    if ratios:
        company_dict["latest_ratios"] = dict(ratios)
    else:
        company_dict["latest_ratios"] = None

    conn.close()
    return company_dict


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Resolve ticker to id
    cursor.execute("SELECT company_id FROM companies WHERE nse = ?", (ticker,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company ticker not found")

    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [company["company_id"]]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE nse = ?", (ticker,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company ticker not found")

    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [company["company_id"]]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE nse = ?", (ticker,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company ticker not found")

    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [company["company_id"]]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(ticker: str, year: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE nse = ?", (ticker,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company ticker not found")

    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [company["company_id"]]

    if year:
        query += " AND year = ?"
        params.append(str(year))

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    # Try different possible locations
    paths_to_check = [
        f"reports/tearsheets/{ticker}_tearsheet.pdf",
        f"output/tearsheets/{ticker}_tearsheet.pdf",
        f"reports/{ticker}_tearsheet.pdf",
        f"output/{ticker}_tearsheet.pdf",
        f"reports/tearsheets/{ticker}.pdf",
        f"output/tearsheets/{ticker}.pdf",
    ]

    for path in paths_to_check:
        if os.path.exists(path):
            return FileResponse(
                path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf"
            )

    raise HTTPException(
        status_code=404, detail="Tearsheet PDF not found for this ticker"
    )
