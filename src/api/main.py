"""
Sprint 6 - FastAPI REST API
Core endpoints exposing companies, ratios, screener, peer comparison,
and NLP insights data from the Nifty 100 platform.

Run with:
    uvicorn src.api.main:app --reload
"""

import sqlite3
from fastapi import FastAPI, HTTPException
from typing import Optional

DB_PATH = "data/nifty100.db"

app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform API",
    description="REST API for company financials, ratios, screener, peer comparison, and NLP insights.",
    version="1.0.0"
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows):
    return [dict(r) for r in rows]


@app.get("/")
def root():
    return {"message": "Nifty 100 Financial Intelligence Platform API is running."}


@app.get("/companies")
def list_companies(limit: int = 50, offset: int = 0):
    """List all companies with pagination."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM companies LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/companies/{company_id}")
def get_company(company_id: str):
    """Get full profile for a single company."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return dict(row)


@app.get("/ratios/{company_id}")
def get_ratios(company_id: str):
    """Get financial ratios for a company."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ?", (company_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Ratios not found for this company")
    return dict(row)


@app.get("/insights/{company_id}")
def get_insights(company_id: str):
    """Get NLP-generated pros/cons insights for a company."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM nlp_insights WHERE company_id = ?", (company_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Insights not found for this company")
    return dict(row)


@app.get("/sectors")
def list_sectors():
    """List all sectors."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sectors").fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/peer-groups/{company_id}")
def get_peer_group(company_id: str):
    """Get peer group members for a company."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM peer_groups WHERE company_id = ?", (company_id,)
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="No peer group found for this company")
    return rows_to_dicts(rows)


@app.get("/stock-prices/{company_id}")
def get_stock_prices(company_id: str, limit: int = 30):
    """Get recent stock price history for a company."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM stock_prices WHERE company_id = ? ORDER BY rowid DESC LIMIT ?",
        (company_id, limit)
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="No stock price data for this company")
    return rows_to_dicts(rows)


@app.get("/market-cap/{company_id}")
def get_market_cap(company_id: str):
    """Get market cap data for a company."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM market_cap WHERE company_id = ?", (company_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Market cap data not found")
    return dict(row)


@app.get("/screener")
def screener(
    min_roe: Optional[float] = None,
    max_pe: Optional[float] = None,
    limit: int = 50
):
    """
    Simple screener endpoint: filter financial_ratios by ROE / P-E
    thresholds when those columns exist under common naming variants.
    """
    conn = get_conn()
    cols = [d[1] for d in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()]

    roe_col = next((c for c in cols if "roe" in c.lower()), None)
    pe_col = next((c for c in cols if c.lower() in ("pe_ratio", "pe", "price_to_earnings")), None)

    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []

    if min_roe is not None and roe_col:
        query += f" AND {roe_col} >= ?"
        params.append(min_roe)
    if max_pe is not None and pe_col:
        query += f" AND {pe_col} <= ?"
        params.append(max_pe)

    query += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}