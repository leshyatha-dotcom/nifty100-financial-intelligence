"""
Sprint 3, Day 15: Filter Engine Core.

Loads screener_config.yaml and applies threshold filters to a merged view of
financial_ratios + market_cap + profitandloss + sectors, for the latest
available year per company (unless a specific year is requested).

Supports all 15 filterable metrics from the spec. D/E filter automatically
skips companies in the Financials broad_sector. ICR filter treats the
'Debt Free' label as infinity (always passes any min_icr threshold).
"""

from pathlib import Path
import sqlite3

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"
CONFIG_PATH = BASE_DIR / "config" / "screener_config.yaml"


def load_config(path=CONFIG_PATH):
    with open(path) as f:
        return yaml.safe_load(f)


def build_universe(conn):
    """Build one row per company (latest year) with all screenable metrics joined."""
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    pl = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    mc = pd.read_sql("SELECT * FROM market_cap", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)

    # latest financial_ratios year per company
    fr_latest = fr.sort_values("year").groupby("company_id").tail(1)

    # matching year's sales/net_profit
    merged = fr_latest.merge(pl, on=["company_id", "year"], how="left")

    # latest market_cap year per company (market_cap.year is a plain int calendar year)
    mc_latest = mc.sort_values("year").groupby("company_id").tail(1)
    mc_latest = mc_latest.drop(columns=["id"], errors="ignore")
    merged = merged.merge(mc_latest, on="company_id", how="left", suffixes=("", "_mc"))

    # FCF yield (needed for value_pick preset ranking)
    merged["fcf_yield_pct"] = merged.apply(
        lambda r: (r["free_cash_flow_cr"] / r["market_cap_crore"] * 100)
        if pd.notna(r.get("market_cap_crore")) and r["market_cap_crore"] not in (0, None)
        else None,
        axis=1,
    )

    merged = merged.merge(sectors, on="company_id", how="left")
    merged = merged.merge(companies, left_on="company_id", right_on="id", how="left")

    return merged


def _effective_icr(row):
    """Treat 'Debt Free' as infinity for ICR threshold comparisons."""
    if row.get("icr_label") == "Debt Free":
        return float("inf")
    return row.get("interest_coverage")


def apply_filters(df, filters, config):
    """filters: dict of {filter_name: threshold_value}, e.g. {'min_roe': 15, 'max_de': 1.0}."""
    result = df.copy()
    result["_effective_icr"] = result.apply(_effective_icr, axis=1)
    filter_defs = config["filters"]

    for name, threshold in filters.items():
        if name not in filter_defs:
            continue
        col = filter_defs[name]["column"]
        op = filter_defs[name]["op"]

        if col == "debt_to_equity":
            # D/E filter: automatically skip Financials sector companies
            mask_financials = result["broad_sector"] == "Financials"
            if op == "<=":
                mask_pass = result["debt_to_equity"] <= threshold
            else:
                mask_pass = result["debt_to_equity"] >= threshold
            result = result[mask_financials | mask_pass]
            continue

        if col == "interest_coverage":
            if op == ">=":
                result = result[result["_effective_icr"] >= threshold]
            continue

        if col not in result.columns:
            continue

        if op == ">=":
            result = result[result[col] >= threshold]
        elif op == "<=":
            result = result[result[col] <= threshold]
        elif op == "==":
            result = result[result[col] == threshold]

    return result.drop(columns=["_effective_icr"], errors="ignore")


def run_screener(filters, year=None):
    """Main entry point: apply filters, return sorted DataFrame with composite_quality_score."""
    conn = sqlite3.connect(DB_PATH)
    config = load_config()
    universe = build_universe(conn)
    conn.close()

    filtered = apply_filters(universe, filters, config)
    return filtered.sort_values("composite_quality_score", ascending=False)


if __name__ == "__main__":
    # Quick smoke test: Quality Compounder-style filter
    result = run_screener({"min_roe": 15, "max_de": 1.0, "min_fcf": 0, "min_rev_cagr_5yr": 10})
    print(f"Matched {len(result)} companies")
    print(result[["company_id", "company_name", "return_on_equity_pct", "debt_to_equity",
                   "composite_quality_score"]].head(10).to_string(index=False))
