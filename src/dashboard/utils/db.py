import sqlite3
import pandas as pd
import streamlit as st
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "nifty100.db",
)


@st.cache_data(ttl=600)
def _run_query(query: str, params: tuple = ()) -> pd.DataFrame:
    """Helper to run queries with Streamlit caching."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    return _run_query("SELECT * FROM companies")


@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    query = "SELECT f.*, c.nse as ticker FROM financial_ratios f JOIN companies c ON f.company_id = c.company_id WHERE 1=1"
    params = []
    if ticker:
        query += " AND c.nse = ?"
        params.append(ticker)
    if year:
        query += " AND f.year = ?"
        params.append(year)
    return _run_query(query, tuple(params))


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    return _run_query(
        "SELECT p.*, c.nse as ticker FROM profitandloss p JOIN companies c ON p.company_id = c.company_id WHERE c.nse = ?",
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    return _run_query(
        "SELECT b.*, c.nse as ticker FROM balancesheet b JOIN companies c ON b.company_id = c.company_id WHERE c.nse = ?",
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    return _run_query(
        "SELECT f.*, c.nse as ticker FROM cashflow f JOIN companies c ON f.company_id = c.company_id WHERE c.nse = ?",
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    return _run_query("SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL")


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    return _run_query("SELECT * FROM companies WHERE sector = ?", (group_name,))


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    query = "SELECT f.year, f.price_to_earnings as pe_ratio, f.price_to_book as pb_ratio FROM financial_ratios f JOIN companies c ON f.company_id = c.company_id WHERE c.nse = ?"
    return _run_query(query, (ticker,))


@st.cache_data(ttl=600)
def get_company(ticker: str) -> pd.DataFrame:
    return _run_query("SELECT * FROM companies WHERE nse = ?", (ticker,))
