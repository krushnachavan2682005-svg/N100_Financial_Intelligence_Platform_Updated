from fastapi import APIRouter

router = APIRouter()
DB_PATH = "nifty100.db"


@router.get("/valuation/{ticker}")
def get_valuation(ticker: str):
    return [
        {"year": 2019, "pe": 20, "pb": 3, "ev_ebitda": 15, "dividend_yield": 1.5},
        {"year": 2024, "pe": 25, "pb": 4, "ev_ebitda": 18, "dividend_yield": 1.2},
    ]


@router.get("/market-cap/{ticker}")
def get_market_cap(ticker: str):
    return {"ticker": ticker, "market_cap": 50000}
