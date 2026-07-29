import sys
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Mock streamlit before importing db
def mock_cache_data(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

mock_st = MagicMock()
mock_st.cache_data = mock_cache_data
sys.modules['streamlit'] = mock_st

# Import the db module
from src.dashboard.utils import db

@pytest.fixture
def mock_run_query():
    with patch('src.dashboard.utils.db._run_query') as mock_query:
        # Create a dummy dataframe to return
        mock_df = pd.DataFrame({'dummy': [1, 2, 3]})
        mock_query.return_value = mock_df
        yield mock_query

def test_get_companies(mock_run_query):
    df = db.get_companies()
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM companies")

def test_get_ratios(mock_run_query):
    df = db.get_ratios(ticker="TCS", year=2023)
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM financial_ratios WHERE 1=1 AND ticker = ? AND year = ?", ("TCS", 2023))

def test_get_ratios_no_params(mock_run_query):
    df = db.get_ratios()
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM financial_ratios WHERE 1=1", ())

def test_get_pl(mock_run_query):
    df = db.get_pl("TCS")
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM pl WHERE ticker = ?", ("TCS",))

def test_get_bs(mock_run_query):
    df = db.get_bs("TCS")
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM bs WHERE ticker = ?", ("TCS",))

def test_get_cf(mock_run_query):
    df = db.get_cf("TCS")
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM cf WHERE ticker = ?", ("TCS",))

def test_get_sectors(mock_run_query):
    df = db.get_sectors()
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL")

def test_get_peers(mock_run_query):
    df = db.get_peers("IT")
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT * FROM companies WHERE sector = ? OR industry = ?", ("IT", "IT"))

def test_get_valuation(mock_run_query):
    df = db.get_valuation("TCS")
    assert isinstance(df, pd.DataFrame)
    mock_run_query.assert_called_with("SELECT ticker, year, pe_ratio, pb_ratio, ev_ebitda FROM financial_ratios WHERE ticker = ?", ("TCS",))
