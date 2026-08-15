import sqlite3
from pathlib import Path

import pytest

from src.analytics.calculator import (
    calculate_financial_ratio_records,
    load_financial_ratios,
    run_screener_verification,
    write_ratio_edge_cases_log,
    _is_financial_sector,
)
from src.analytics.cagr import calculate_cagr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def _seed_database(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO companies (company_id, company_name) VALUES (?, ?)",
            ("C001", "Example Industries"),
        )
        for year, sales in zip(range(2018, 2024), (100, 110, 120, 140, 170, 200)):
            connection.execute(
                """INSERT INTO profitandloss
                   (company_id, year, sales, operating_profit, interest, net_profit, eps, dividend_payout_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("C001", year, sales, sales * 0.2, 10, sales * 0.1, 2.5, 15),
            )
            connection.execute(
                """INSERT INTO balancesheet
                   (company_id, year, equity_capital, reserves, borrowings, other_liabilities, total_assets)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("C001", year, 50, 50, 50, 0, 150),
            )
            connection.execute(
                """INSERT INTO cashflow
                   (company_id, year, cash_from_operating_activity, cash_from_investing_activity)
                   VALUES (?, ?, ?, ?)""",
                ("C001", year, sales * 0.15, -sales * 0.1),
            )
        connection.commit()
    finally:
        connection.close()


def test_calculate_financial_ratios_for_latest_multi_year_record(tmp_path):
    database_path = tmp_path / "ratios.db"
    _seed_database(database_path)
    connection = sqlite3.connect(database_path)
    try:
        records = calculate_financial_ratio_records(connection)
    finally:
        connection.close()

    latest = next(record for record in records if record["year"] == 2023)
    assert len(records) == 6
    assert latest["net_margin_pct"] == pytest.approx(10.0)
    assert latest["debt_to_equity"] == pytest.approx(0.5)
    assert latest["interest_coverage"] == pytest.approx(4.0)
    assert latest["return_on_equity_pct"] == pytest.approx(20.0)
    assert latest["return_on_capital_employed_pct"] == pytest.approx(26.6666666666)
    assert latest["asset_turnover"] == pytest.approx(200 / 150)
    assert latest["free_cash_flow"] == pytest.approx(10.0)
    assert latest["fcf_to_net_profit"] == pytest.approx(0.5)
    assert latest["cfo_to_operating_profit"] == pytest.approx(0.75)
    assert latest["sales_cagr_3y"] == pytest.approx(calculate_cagr(120, 200, 3))
    assert latest["sales_cagr_5y"] == pytest.approx(calculate_cagr(100, 200, 5))
    assert latest["current_ratio"] is None


def test_load_financial_ratios_upserts_calculated_records(tmp_path):
    database_path = tmp_path / "ratios.db"
    _seed_database(database_path)

    assert load_financial_ratios(database_path) == 6
    assert load_financial_ratios(database_path) == 6

    connection = sqlite3.connect(database_path)
    try:
        assert (
            connection.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
            == 6
        )
        latest = connection.execute(
            "SELECT sales_cagr_5y, free_cash_flow FROM financial_ratios WHERE company_id = ? AND year = ?",
            ("C001", 2023),
        ).fetchone()
        assert latest[0] == pytest.approx(calculate_cagr(100, 200, 5))
        assert latest[1] == pytest.approx(10.0)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_sales_cagr_flags_are_stored_for_insufficient_history(tmp_path):
    database_path = tmp_path / "ratios.db"
    _seed_database(database_path)
    connection = sqlite3.connect(database_path)
    try:
        records = calculate_financial_ratio_records(connection)
    finally:
        connection.close()

    earliest = next(record for record in records if record["year"] == 2018)
    assert earliest["sales_cagr_3y"] is None
    assert earliest["sales_cagr_3y_flag"] == "INSUFFICIENT"
    assert earliest["sales_cagr_5y_flag"] == "INSUFFICIENT"


@pytest.mark.parametrize(
    ("sector", "expected"),
    [
        ("Banks", True),
        ("Finance", True),
        ("NBFC - Housing", True),
        ("IT - Software", False),
        (None, False),
    ],
)
def test_financial_sector_carve_out(sector, expected):
    assert _is_financial_sector(sector) is expected


def test_write_ratio_edge_cases_log_flags_large_roe_differences(tmp_path):
    records = [
        {
            "company_id": "C001",
            "year": 2023,
            "return_on_equity_pct": 20.0,
            "return_on_capital_employed_pct": 10.0,
            "_audit_context": {
                "source_ratio_roe": 10.0,
                "source_ratio_roce": None,
                "source_roe_pct": None,
                "source_roce_pct": None,
            },
        }
    ]
    log_path = tmp_path / "ratio_edge_cases.log"
    count = write_ratio_edge_cases_log(records, log_path)
    contents = log_path.read_text(encoding="utf-8")
    assert count == 1
    assert "C001,2023,ROE,20.0000,10.0000,source_ratios.roe_pct,10.0000" in contents


def test_load_financial_ratios_writes_audit_deliverables(tmp_path):
    database_path = tmp_path / "ratios.db"
    _seed_database(database_path)
    output_dir = tmp_path / "output"
    capital_path = output_dir / "capital_allocation.csv"
    edge_log_path = output_dir / "ratio_edge_cases.log"

    import src.analytics.calculator as calculator_module

    original_output_dir = calculator_module.OUTPUT_DIR
    original_capital_path = calculator_module.CAPITAL_ALLOCATION_CSV
    original_edge_log_path = calculator_module.RATIO_EDGE_CASES_LOG
    calculator_module.OUTPUT_DIR = output_dir
    calculator_module.CAPITAL_ALLOCATION_CSV = capital_path
    calculator_module.RATIO_EDGE_CASES_LOG = edge_log_path
    try:
        assert load_financial_ratios(database_path) == 6
        assert capital_path.exists()
        assert edge_log_path.exists()
        assert (
            "company_id,year,cfo_sign,cfi_sign,cff_sign,pattern_label"
            in capital_path.read_text(encoding="utf-8")
        )
    finally:
        calculator_module.OUTPUT_DIR = original_output_dir
        calculator_module.CAPITAL_ALLOCATION_CSV = original_capital_path
        calculator_module.RATIO_EDGE_CASES_LOG = original_edge_log_path


def test_run_screener_verification(tmp_path):
    database_path = tmp_path / "ratios.db"
    _seed_database(database_path)
    load_financial_ratios(database_path)
    connection = sqlite3.connect(database_path)
    try:
        result = run_screener_verification(connection)
    finally:
        connection.close()
    assert result["total_matches"] >= 1
    assert result["latest_year_matches"] >= 1
