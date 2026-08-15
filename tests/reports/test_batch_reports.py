import os
from src.reports.tearsheet import batch_generate_pdfs
from src.reports.sector_report import batch_generate_sector_reports


def test_batch_generate_tearsheets(tmp_path):
    out_dir = os.path.join(str(tmp_path), "tearsheets")
    log_dir = os.path.join(str(tmp_path), "logs")

    # We pass a dummy db path to trigger the fallback mock data in tearsheet.py
    generated = batch_generate_pdfs("dummy.db", out_dir, log_dir)

    # Mock data has 5 companies with 10 years, 1 with 2 years (skipped)
    assert len(generated) == 5

    for path in generated:
        assert os.path.exists(path)
        # Check if file size > 30KB
        # (A PDF with a few charts and text is typically > 10KB. We will check > 5KB for safety since it's just dummy charts)
        assert os.path.getsize(path) > 5000

    skip_log = os.path.join(log_dir, "skipped_tearsheets.csv")
    assert os.path.exists(skip_log)


def test_batch_generate_sector_reports(tmp_path):
    out_dir = os.path.join(str(tmp_path), "sectors")

    # Pass dummy db path to trigger fallback mock data
    generated = batch_generate_sector_reports("dummy.db", out_dir)

    # Mock data has 2 sectors (IT, Financials)
    assert len(generated) == 2

    for path in generated:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000  # Basic pdf is > 1KB
