import os
from PyPDF2 import PdfReader
from src.reports.portfolio_report import get_trend_arrow, generate_portfolio_report


def test_get_trend_arrow():
    # Regular metrics (higher is better)
    assert get_trend_arrow(110, 100, lower_is_better=False) == "^"  # Improved
    assert get_trend_arrow(90, 100, lower_is_better=False) == "v"  # Declined
    assert get_trend_arrow(101, 100, lower_is_better=False) == "->"  # Flat (<= 2%)

    # Lower is better (e.g. Debt/Equity)
    assert get_trend_arrow(0.8, 1.0, lower_is_better=True) == "^"  # Improved
    assert get_trend_arrow(1.2, 1.0, lower_is_better=True) == "v"  # Declined
    assert get_trend_arrow(1.01, 1.0, lower_is_better=True) == "->"  # Flat


def test_generate_portfolio_report(tmp_path):
    out_dir = str(tmp_path)
    out_path = os.path.join(out_dir, "portfolio_summary.pdf")

    # Pass dummy db to trigger mock data
    generate_portfolio_report("dummy.db", out_path)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 1000

    # The mock data has 1 company (TCS), so it should be 1 page long
    reader = PdfReader(out_path)
    assert len(reader.pages) == 1
