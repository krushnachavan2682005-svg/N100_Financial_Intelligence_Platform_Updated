# Nifty 100 Financial Intelligence Platform

## Executive Summary
An advanced analytical platform designed for parsing, ingesting, clustering, and querying fundamental data of Nifty 100 companies. 

## Architecture
- **ETL Engine**: Ingests unstructured PDFs, standardises schema, validates data via DQ engine.
- **SQLite DB (`nifty100.db`)**: Indexed schema supporting fast analytical queries.
- **FastAPI API Server**: Highly concurrent, RESTful endpoints.
- **Streamlit Dashboard**: 8-screen comprehensive UI.

## Installation & Launch
1. **API Server**:
   `uvicorn src.api.main:app --port 8000`
2. **Streamlit Dashboard**:
   `streamlit run src/dashboard/app.py`
3. **Database Build**:
   `python run_presets.py` or equivalent builder.
4. **Test Suite Generation**:
   `pytest tests/ --html=reports/pytest_report.html`
