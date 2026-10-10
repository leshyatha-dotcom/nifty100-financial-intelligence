PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS companies;
CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

DROP TABLE IF EXISTS profitandloss;
CREATE TABLE profitandloss (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS balancesheet;
CREATE TABLE balancesheet (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS cashflow;
CREATE TABLE cashflow (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS analysis;
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS documents;
CREATE TABLE documents (
    id INTEGER,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    PRIMARY KEY (company_id, year, id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS prosandcons;
CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS sectors;
CREATE TABLE sectors (
    id INTEGER,
    company_id TEXT PRIMARY KEY,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS stock_prices;
CREATE TABLE stock_prices (
    id INTEGER,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS market_cap;
CREATE TABLE market_cap (
    id INTEGER,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS financial_ratios;
CREATE TABLE financial_ratios (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    roce_pct REAL,
    roa_pct REAL,
    high_leverage_flag INTEGER,
    icr_label TEXT,
    icr_warning_flag INTEGER,
    net_debt_cr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_5yr_flag TEXT,
    pat_cagr_5yr REAL,
    pat_cagr_5yr_flag TEXT,
    eps_cagr_5yr REAL,
    eps_cagr_5yr_flag TEXT,
    cfo_quality_score REAL,
    cfo_quality_label TEXT,
    capex_intensity_pct REAL,
    capex_intensity_label TEXT,
    fcf_conversion_pct REAL,
    composite_quality_score REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

DROP TABLE IF EXISTS peer_groups;
CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
