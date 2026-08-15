import pandas as pd
import pytest
from src.screener.engine import filter_stocks


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "ticker": ["A", "B", "C", "D", "E"],
            "sector": ["IT", "Financials", "FMCG", "Auto", "IT"],
            "roe": [15.0, 10.0, 25.0, 8.0, 20.0],
            "debt_to_equity": [0.5, 3.0, 0.1, 1.5, 0.0],
            "icr": [5.0, 2.0, "Debt Free", 1.5, None],
            "market_cap": [1000, 5000, 2000, 500, 3000],
        }
    )


def test_threshold_filters(sample_data):
    criteria = {"roe_min": 15.0, "market_cap_min": 2000}
    filtered = filter_stocks(sample_data, criteria)
    assert len(filtered) == 2
    assert set(filtered["ticker"]) == {"C", "E"}


def test_financials_sector_de_exemption(sample_data):
    criteria = {"d_e_max": 1.0}
    filtered = filter_stocks(sample_data, criteria)
    assert len(filtered) == 4
    assert set(filtered["ticker"]) == {"A", "B", "C", "E"}


def test_debt_free_icr_behavior(sample_data):
    criteria = {"icr_min": 4.0}
    filtered = filter_stocks(sample_data, criteria)
    assert len(filtered) == 3
    assert set(filtered["ticker"]) == {"A", "C", "E"}


def test_composite_quality_score_added(sample_data):
    criteria = {}
    filtered = filter_stocks(sample_data, criteria)
    assert "composite_quality_score" in filtered.columns
    assert (filtered["composite_quality_score"] >= 0.0).all()
    assert (filtered["composite_quality_score"] <= 100.0).all()


def test_preset_quality_compounder():

    # Mocking os.path.exists and yaml.safe_load is overkill, just pass data directly for the test
    df = pd.DataFrame(
        {
            "ticker": ["A", "B"],
            "roe": [20.0, 10.0],
            "debt_to_equity": [0.5, 1.5],
            "fcf": [100, -50],
            "revenue_cagr_5yr": [15.0, 5.0],
        }
    )
    criteria = {
        "roe_min": 15.0,
        "d_e_max": 1.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 10.0,
    }
    filtered = filter_stocks(df, criteria)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "A"


def test_preset_turnaround_watch():
    df = pd.DataFrame(
        {
            "ticker": ["A", "B"],
            "revenue_cagr_3yr": [15.0, 5.0],
            "fcf": [50, -10],
            "debt_to_equity": [1.0, 2.0],
            "debt_to_equity_prev": [1.5, 1.0],  # A declining, B increasing
        }
    )
    criteria = {"revenue_cagr_3yr_min": 10.0, "fcf_min": 0, "d_e_declining_yoy": True}
    filtered = filter_stocks(df, criteria)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "A"


def test_load_presets(tmp_path):
    from src.screener.engine import load_presets
    import yaml

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        yaml.dump({"presets": {"test": {"criteria": {"roe_min": 10}}}})
    )
    presets = load_presets(str(config_file))
    assert "test" in presets
    assert presets["test"]["criteria"]["roe_min"] == 10


def test_composite_score_calculation():
    from src.screener.engine import calculate_composite_score

    df = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "sector": ["IT", "IT", "IT"],
            "roe": [20.0, 10.0, 5.0],
            "debt_to_equity": [0.5, 1.5, 2.0],
        }
    )
    scored = calculate_composite_score(df)
    assert "composite_quality_score" in scored.columns
    assert scored["composite_quality_score"].max() <= 100.0
    assert scored["composite_quality_score"].min() >= 0.0
    # A should be better than B and C
    score_A = scored[scored["ticker"] == "A"]["composite_quality_score"].iloc[0]
    score_C = scored[scored["ticker"] == "C"]["composite_quality_score"].iloc[0]
    assert score_A > score_C


def test_excel_export(tmp_path):
    from src.screener.exporter import export_screener_results
    import os

    out_file = tmp_path / "test_output.xlsx"
    df = pd.DataFrame(
        {
            "ticker": ["A", "B"],
            "composite_quality_score": [90.0, 40.0],
            "roe": [20.0, 10.0],
        }
    )
    results = {"Quality Compounder": df}
    criteria = {"Quality Compounder": {"roe_min": 15.0}}
    export_screener_results(results, str(out_file), criteria)
    assert os.path.exists(out_file)
    # Check it can be read
    read_df = pd.read_excel(str(out_file), sheet_name="Quality Compounder")
    assert len(read_df) == 2
    assert "composite_quality_score" in read_df.columns
