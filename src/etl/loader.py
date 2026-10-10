"""
Excel loader for the Nifty 100 Financial Intelligence Platform.

Per the project spec (Section 5, "Load note"):
  - Core files (companies, profitandloss, balancesheet, cashflow, analysis,
    documents, prosandcons) use pd.read_excel(path, header=1) — row 0 is a
    metadata/title row, row 1 is the real header.
  - Supplementary files (sectors, stock_prices, market_cap, financial_ratios,
    peer_groups) use header=0.

Every table's company_id column is normalised via normalize_ticker(); every
year-like column is normalised via normalize_year().
"""

from pathlib import Path
import pandas as pd

from normaliser import normalize_ticker, normalize_year

# Core files: header row is row index 1 (0-indexed) -> header=1
CORE_FILES = {
    "companies": {"path": "data/raw/companies.xlsx", "header": 1, "year_col": None},
    "profitandloss": {"path": "data/raw/profitandloss.xlsx", "header": 1, "year_col": "year"},
    "balancesheet": {"path": "data/raw/balancesheet.xlsx", "header": 1, "year_col": "year"},
    "cashflow": {"path": "data/raw/cashflow.xlsx", "header": 1, "year_col": "year"},
    "analysis": {"path": "data/raw/analysis.xlsx", "header": 1, "year_col": None},
    "documents": {"path": "data/raw/documents.xlsx", "header": 1, "year_col": None},  # 'Year' handled specially
    "prosandcons": {"path": "data/raw/prosandcons.xlsx", "header": 1, "year_col": None},
}

# Supplementary files: header=0
SUPPLEMENTARY_FILES = {
    "sectors": {"path": "data/supporting/sectors.xlsx", "header": 0, "year_col": None},
    "stock_prices": {"path": "data/supporting/stock_prices.xlsx", "header": 0, "year_col": None},  # 'date' not 'year'
    "market_cap": {"path": "data/supporting/market_cap.xlsx", "header": 0, "year_col": None},  # numeric year, no normalise needed
    "financial_ratios": {"path": "data/supporting/financial_ratios.xlsx", "header": 0, "year_col": "year"},
    "peer_groups": {"path": "data/supporting/peer_groups.xlsx", "header": 0, "year_col": None},
}

ALL_FILES = {**CORE_FILES, **SUPPLEMENTARY_FILES}


def load_table(name, base_dir):
    """Load one source file into a normalised DataFrame."""
    cfg = ALL_FILES[name]
    path = Path(base_dir) / cfg["path"]
    df = pd.read_excel(path, header=cfg["header"])

    rows_in = len(df)
    rejected = 0

    # --- ticker normalisation ---
    id_col = "company_id" if "company_id" in df.columns else ("id" if name == "companies" else None)
    if id_col:
        df[id_col] = df[id_col].apply(normalize_ticker)
        before = len(df)
        df = df[df[id_col].notna()]
        rejected += before - len(df)

    # --- year normalisation ---
    if cfg["year_col"] and cfg["year_col"] in df.columns:
        df[cfg["year_col"]] = df[cfg["year_col"]].apply(normalize_year)
        before = len(df)
        df = df[df[cfg["year_col"]] != "PARSE_ERROR"]
        rejected += before - len(df)

    # documents.xlsx uses capital 'Year' (integer calendar year) - cast to int, no month normalisation needed
    if name == "documents" and "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    rows_out = len(df)
    return df, {"table": name, "rows_in": rows_in, "rows_out": rows_out, "rejected": rejected}


def load_all(base_dir="."):
    """Load every one of the 12 source files. Returns (dict of DataFrames, list of audit rows)."""
    frames = {}
    audit_rows = []
    for name in ALL_FILES:
        df, audit = load_table(name, base_dir)
        frames[name] = df
        audit_rows.append(audit)
    return frames, audit_rows


if __name__ == "__main__":
    import time

    t0 = time.time()
    frames, audit_rows = load_all(base_dir=Path(__file__).resolve().parents[2])
    runtime = time.time() - t0

    print(f"Loaded {len(frames)} tables in {runtime:.2f}s\n")
    for a in audit_rows:
        print(f"  {a['table']:<18} rows_in={a['rows_in']:<6} rows_out={a['rows_out']:<6} rejected={a['rejected']}")
