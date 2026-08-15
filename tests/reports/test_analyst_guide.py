import os
from PyPDF2 import PdfReader


def test_analyst_guide_pdf():
    pdf_path = "docs/analyst_guide.pdf"
    assert os.path.exists(pdf_path), "PDF does not exist"

    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    assert num_pages >= 10, f"PDF only has {num_pages} pages, expected >= 10"
