PRAGMA foreign_keys = ON;

-- N100 Financial Intelligence Platform: Sprint 1 / Day 04
-- Monetary values and percentages are stored as REAL. Dates/timestamps use
-- ISO-8601 TEXT so SQLite remains portable across ingestion environments.

CREATE TABLE IF NOT EXISTS sectors (
    sector_id TEXT PRIMARY KEY,
    sector_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    sector_id TEXT,
    bse TEXT,
    nse TEXT,
    isin TEXT UNIQUE,
    market_cap_cr REAL,
    current_price REAL,
    high_low TEXT,
    stock_pe REAL,
    book_value REAL,
    dividend_yield_pct REAL,
    source_roce_pct REAL,
    source_roe_pct REAL,
    face_value REAL,
    eps REAL,
    debt_cr REAL,
    source_folder TEXT,
    source_name TEXT,
    updated_at TEXT,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    company_name TEXT,
    nse TEXT,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_pct REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_pct REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout_pct REAL,
    reporting_currency TEXT,
    source_name TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    company_name TEXT,
    nse TEXT,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_assets REAL,
    total_assets REAL,
    reporting_currency TEXT,
    source_name TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    company_name TEXT,
    nse TEXT,
    cash_from_operating_activity REAL,
    cash_from_investing_activity REAL,
    cash_from_financing_activity REAL,
    net_cash_flow REAL,
    reporting_currency TEXT,
    source_name TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_ratios (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    company_name TEXT,
    nse TEXT,
    roe_pct REAL,
    roce_pct REAL,
    debtor_days REAL,
    inventory_days REAL,
    days_payable REAL,
    cash_conversion_cycle REAL,
    working_capital_days REAL,
    source_name TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    current_ratio REAL,
    quick_ratio REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    gross_margin_pct REAL,
    net_margin_pct REAL,
    return_on_assets_pct REAL,
    return_on_equity_pct REAL,
    return_on_capital_employed_pct REAL,
    asset_turnover REAL,
    earnings_per_share REAL,
    price_to_earnings REAL,
    price_to_book REAL,
    dividend_yield_pct REAL,
    sales_cagr_3y REAL,
    sales_cagr_5y REAL,
    sales_cagr_3y_flag TEXT,
    sales_cagr_5y_flag TEXT,
    free_cash_flow REAL,
    fcf_to_net_profit REAL,
    cfo_to_operating_profit REAL,
    source_name TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT NOT NULL,
    price_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    adjusted_close_price REAL,
    volume INTEGER,
    source_name TEXT,
    PRIMARY KEY (company_id, price_date),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- One row associates a company with a named peer group; a group can contain
-- many companies and a company can participate in multiple groups.
CREATE TABLE IF NOT EXISTS peer_groups (
    peer_group_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    peer_group_name TEXT NOT NULL,
    description TEXT,
    created_at TEXT,
    PRIMARY KEY (peer_group_id, company_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis (
    analysis_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    rating TEXT,
    target_price REAL,
    analyst_name TEXT,
    source_name TEXT,
    created_at TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    document_date TEXT,
    source_url TEXT,
    storage_path TEXT,
    source_name TEXT,
    retrieved_at TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prosandcons (
    prosandcons_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    analysis_id INTEGER,
    sentiment TEXT NOT NULL CHECK (sentiment IN ('pro', 'con')),
    item_text TEXT NOT NULL,
    source_name TEXT,
    created_at TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES analysis(analysis_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);
