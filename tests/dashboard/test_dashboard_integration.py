import sys
import time
from unittest.mock import MagicMock


# Mock streamlit before importing db
def mock_cache_data(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


mock_st = MagicMock()
mock_st.cache_data = mock_cache_data
sys.modules["streamlit"] = mock_st

from src.dashboard.utils import db


def test_get_company_invalid():
    """Test handling of invalid ticker."""
    df = db.get_company("INVALID_TICKER")
    assert df.empty


def test_get_ratios_empty():
    """Test ratios for missing company."""
    df = db.get_ratios("NONEXISTENT")
    assert df.empty


def test_query_performance():
    """Test performance of fetching large datasets."""
    start_time = time.time()
    df = db.get_companies()
    end_time = time.time()
    assert (end_time - start_time) < 3.0, "Company fetching took longer than 3 seconds"

    start_time = time.time()
    df = db.get_ratios()
    end_time = time.time()
    assert (end_time - start_time) < 3.0, "Ratios fetching took longer than 3 seconds"


def test_partial_year_handling():
    """Test db logic handles missing/NaN data gracefully."""
    # This is an integration check to ensure DB doesn't throw errors
    df = db.get_pl("TCS")
    if not df.empty:
        # Check that NaN doesn't break dataframe structure
        assert "sales" in df.columns
        # NaN is naturally handled by pandas
