import pandas as pd
from unittest.mock import patch
from src.analytics.cashflow_kpis import (
    calculate_cfo_quality,
    get_cfo_label,
    get_capex_label,
    generate_cashflow_kpis,
)


def test_calculate_cfo_quality():
    # Regular
    assert calculate_cfo_quality([100, 200], [50, 50]) == 3.0

    # Negative PAT but Positive CFO
    assert calculate_cfo_quality([100, 100], [-50, -10]) == 1.5

    # Zero PAT but Positive CFO
    assert calculate_cfo_quality([100, 100], [0, 0]) == 1.5


def test_get_cfo_label():
    assert get_cfo_label(1.2) == "High Quality"
    assert get_cfo_label(0.8) == "Moderate"
    assert get_cfo_label(0.4) == "Accrual Risk"
    assert get_cfo_label(None) == "Unknown"


def test_get_capex_label():
    assert get_capex_label(2.5) == "Asset Light"
    assert get_capex_label(5.0) == "Moderate"
    assert get_capex_label(10.0) == "Capital Intensive"
    assert get_capex_label(None) == "Unknown"


@patch("src.analytics.cashflow_kpis.sqlite3.connect")
@patch("src.analytics.cashflow_kpis.pd.read_sql_query")
def test_generate_cashflow_kpis(mock_read_sql, mock_connect):
    # Mock data that includes distress and deleveraging
    mock_df = pd.DataFrame(
        {
            "company_id": [1, 1],
            "company_name": ["TCS", "TCS"],
            "sector": ["IT", "IT"],
            "year": [2022, 2023],
            "cfo": [1000, -500],  # CFO drops negative
            "cfi": [-200, -100],
            "cff": [-500, 1000],  # CFF goes positive
            "pat": [800, -200],
            "sales": [5000, 6000],
            "borrowings": [2000, 1500],
        }
    )
    mock_read_sql.return_value = mock_df

    result = generate_cashflow_kpis("dummy.db")

    assert not result.empty

    tcs = result.iloc[0]

    # CapEx = abs(-100) / 6000 * 100 = 1.66% -> Asset Light
    assert tcs["capex_label"] == "Asset Light"

    # Distress: CFO < 0 (-500) and CFF > 0 (1000) -> True
    assert tcs["distress_flag"] == True

    # Deleveraging: CFF < 0 -> False (CFF is 1000)
    assert tcs["deleveraging_flag"] == False
