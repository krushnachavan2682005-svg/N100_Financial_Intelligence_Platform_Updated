import os
from PyPDF2 import PdfReader
from src.reports.tearsheet import generate_tearsheet


def test_generate_tearsheet(tmp_path):
    output_dir = str(tmp_path)
    output_pdf = os.path.join(output_dir, "TEST_tearsheet.pdf")

    # Should not raise exception
    generate_tearsheet("TEST", output_pdf)

    assert os.path.exists(output_pdf)

    # Verify it is strictly 2 pages
    reader = PdfReader(output_pdf)
    assert len(reader.pages) == 2
