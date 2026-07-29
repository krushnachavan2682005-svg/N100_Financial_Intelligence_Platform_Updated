# N100 Financial Intelligence Platform
This project currently uses a temporary Kaggle Top 92 surrogate dataset for ETL development because the official source files are pending.

## How to Run the Dashboard
To start the interactive Streamlit dashboard, run the following command from the project root:
```bash
streamlit run src/dashboard/app.py
```

## Dashboard Features
The application features 8 distinct screens for comprehensive financial analysis:

1. **Home Screen (`01_home.py`)**: Displays key metrics (ROE, P/E, D/E, Total Companies, etc.), a sector breakdown donut chart, and a table of top companies sorted by composite quality score. Includes a year selector for dynamic updates.
2. **Company Profile (`02_profile.py`)**: Deep dive into individual companies. Includes a search functionality, 6 specific KPIs, interactive 10-year line and bar charts (ROE, ROCE, Revenue, Net Profit), and a metric-driven Pros/Cons section.
3. **Screener (`03_screener.py`)**: A powerful stock screener with 10 metric sliders and 6 pre-built strategy presets (Quality, Value, Growth, etc.). Live updating result counts and CSV download capabilities are built-in.
4. **Peer Comparison (`04_peers.py`)**: Compare companies within their sector using interactive Plotly radar charts alongside a comprehensive sector KPI table highlighting the benchmark company.
5. **Trend Analysis (`05_trends.py`)**: Interactive 10-year Plotly line charts displaying up to 3 selected metrics simultaneously, annotated with YoY percentage changes.
6. **Sector Analysis (`06_sectors.py`)**: Scatter bubble charts mapping Revenue vs ROE with bubble sizes indicating Market Cap. Includes sector median KPI bar charts for relative performance assessment.
7. **Capital Allocation (`07_capital.py`)**: A visual Treemap mapping companies to specific capital allocation patterns like Consistent Compounders or Debt Repayers based on their market capitalization.
8. **Annual Reports (`08_reports.py`)**: Document repository allowing users to search and download historical Annual Reports (PDFs) from BSE, complete with live availability validation badges.