import sqlite3
import pandas as pd
import streamlit as st
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'nifty100.db')

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
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND ticker = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)
    return _run_query(query, tuple(params))

@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    return _run_query("SELECT * FROM pl WHERE ticker = ?", (ticker,))

@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    return _run_query("SELECT * FROM bs WHERE ticker = ?", (ticker,))

@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    return _run_query("SELECT * FROM cf WHERE ticker = ?", (ticker,))

@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    # Assuming 'sector' column in 'companies' table
    return _run_query("SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL")

@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    # Assuming group_name corresponds to 'sector' or 'industry'
    return _run_query("SELECT * FROM companies WHERE sector = ? OR industry = ?", (group_name, group_name))

@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    # Placeholder querying financial_ratios for valuation metrics if a specific table doesn't exist
    query = "SELECT ticker, year, pe_ratio, pb_ratio, ev_ebitda FROM financial_ratios WHERE ticker = ?"
    try:
        return _run_query(query, (ticker,))
    except Exception:
        # Fallback if specific columns are missing
        return pd.DataFrame()
