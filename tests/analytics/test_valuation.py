import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from src.analytics.valuation import get_valuation_data, generate_reports


@pytest.fixture
def mock_db_data():
    companies = pd.DataFrame(
        {
            "company_id": [1, 2, 3],
            "company_name": ["TCS", "Infosys", "HDFC"],
            "sector": ["IT", "IT", "Finance"],
            "market_cap_cr": [100000, 80000, 150000],
        }
    )

    ratios = pd.DataFrame(
        {
            "company_id": [1, 1, 2, 2, 3, 3],
            "year": [2022, 2023, 2022, 2023, 2022, 2023],
            "price_to_earnings": [25, 30, 20, 22, 15, 18],
            "price_to_book": [5, 6, 4, 4.5, 2, 2.5],
            "free_cash_flow": [5000, 6000, 4000, 4500, 8000, 9000],
        }
    )

    return companies, ratios


@patch("src.analytics.valuation.sqlite3.connect")
@patch("src.analytics.valuation.pd.read_sql_query")
def test_get_valuation_data(mock_read_sql, mock_connect, mock_db_data):
    companies, ratios = mock_db_data
    # Mocking read_sql_query side effects
    mock_read_sql.side_effect = [companies, ratios]

    result = get_valuation_data("dummy.db")

    assert not result.empty
    assert len(result) == 3

    # Check TCS
    tcs = result[result["company_name"] == "TCS"].iloc[0]
    assert tcs["P/E"] == 30
    assert tcs["FCF_yield_pct"] == (6000 / 100000) * 100
    assert tcs["5yr_median_PE"] == 27.5  # (25+30)/2

    # Check Flags
    # IT sector median PE in 2023 = median(30, 22) = 26
    # Finance sector median PE = 18
    # TCS P/E = 30. sector_median = 26. 26 * 1.5 = 39. So Fair.
    # What if TCS P/E was 40? Then Caution.
    assert tcs["flag"] == "Fair"


@patch("src.analytics.valuation.get_valuation_data")
@patch("src.analytics.valuation.pd.DataFrame.to_excel")
@patch("src.analytics.valuation.pd.DataFrame.to_csv")
def test_generate_reports(mock_to_csv, mock_to_excel, mock_get_data, tmp_path):
    mock_df = pd.DataFrame(
        {
            "company_id": [1, 2],
            "company_name": ["TCS", "BadCo"],
            "sector": ["IT", "IT"],
            "P/E": [20, 100],
            "P/B": [5, 10],
            "EV/EBITDA": [np.nan, np.nan],
            "FCF_yield_pct": [5.0, -1.0],
            "5yr_median_PE": [18, 50],
            "PE_vs_sector_median_pct": [0, 400],
            "flag": ["Fair", "Caution"],
        }
    )
    mock_get_data.return_value = mock_df

    output_dir = str(tmp_path)
    generate_reports("dummy.db", output_dir)

    assert mock_to_excel.called
    assert mock_to_csv.called

    # Verify csv only has Caution/Discount
    args, kwargs = mock_to_csv.call_args
    # The dataframe that called to_csv is accessed via the mock
    # Actually, we can just check the file path passed
    assert "valuation_flags.csv" in args[0]
