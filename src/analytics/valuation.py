"""Module 6 - Valuation & Market Data Module.

Uses market_cap.xlsx (loaded into the market_cap table) plus financial_ratios
to compute valuation summaries, dividend/FCF yield rankings, and
over/under-valuation flags relative to each company's sector median.
"""
import sqlite3

import pandas as pd

DB_PATH = "data/nifty100.db"


def _load_frames(db_path: str = DB_PATH) -> dict:
    with sqlite3.connect(db_path) as conn:
        market_cap = pd.read_sql("SELECT * FROM market_cap", conn)
        financial_ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
        sectors = pd.read_sql("SELECT * FROM sectors", conn)
        companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    return {
        "market_cap": market_cap,
        "financial_ratios": financial_ratios,
        "sectors": sectors,
        "companies": companies,
    }


def build_valuation_summary(db_path: str = DB_PATH) -> pd.DataFrame:
    """Build the per-company valuation summary with current + 5yr median
    multiples, sector rank, and Caution/Discount badges.
    """
    d = _load_frames(db_path)
    mc = d["market_cap"].copy()
    if mc.empty:
        return pd.DataFrame()

    mc["year"] = mc["year"].astype(int)
    latest_year = mc["year"].max()

    current = mc[mc["year"] == latest_year].copy()
    hist = mc[mc["year"] >= latest_year - 4]  # up to 5 years incl. latest

    median_5yr = (
        hist.groupby("company_id")[["pe_ratio", "pb_ratio", "ev_ebitda"]]
        .median()
        .add_suffix("_5yr_median")
        .reset_index()
    )

    out = current.merge(median_5yr, on="company_id", how="left")
    out = out.merge(d["sectors"][["company_id", "broad_sector"]], on="company_id", how="left")
    out = out.merge(d["companies"], left_on="company_id", right_on="id", how="left")

    # Sector median P/E for overvaluation flag + rank
    sector_pe_median = out.groupby("broad_sector")["pe_ratio"].transform("median")
    out["sector_pe_median"] = sector_pe_median
    out["pe_vs_sector_pct"] = (out["pe_ratio"] / out["sector_pe_median"] - 1) * 100

    def _badge(row):
        if pd.isna(row["sector_pe_median"]) or row["sector_pe_median"] == 0:
            return None
        if row["pe_ratio"] > row["sector_pe_median"] * 1.5:
            return "Caution"
        if row["pe_ratio"] < row["sector_pe_median"] * 0.7:
            return "Discount"
        return None

    out["valuation_badge"] = out.apply(_badge, axis=1)
    out["sector_pe_rank"] = out.groupby("broad_sector")["pe_ratio"].rank(method="min")

    # FCF yield: FCF / market cap * 100, joined from latest financial_ratios year
    fr = d["financial_ratios"].copy()
    fr_latest = fr.sort_values("year").groupby("company_id").tail(1)
    out = out.merge(
        fr_latest[["company_id", "free_cash_flow_cr"]], on="company_id", how="left"
    )
    out["fcf_yield_pct"] = (
        out["free_cash_flow_cr"] / out["market_cap_crore"] * 100
    ).round(2)

    cols = [
        "company_id", "company_name", "broad_sector", "year",
        "market_cap_crore", "enterprise_value_crore",
        "pe_ratio", "pe_ratio_5yr_median", "sector_pe_median", "pe_vs_sector_pct", "sector_pe_rank",
        "pb_ratio", "pb_ratio_5yr_median",
        "ev_ebitda", "ev_ebitda_5yr_median",
        "dividend_yield_pct", "fcf_yield_pct", "valuation_badge",
    ]
    out = out[[c for c in cols if c in out.columns]].sort_values("company_id").reset_index(drop=True)
    return out


def build_valuation_flags(summary: pd.DataFrame) -> pd.DataFrame:
    """Extract just the flagged (Caution/Discount) companies with a rationale."""
    flagged = summary[summary["valuation_badge"].notna()].copy()

    def _rationale(row):
        direction = "above" if row["valuation_badge"] == "Caution" else "below"
        return (
            f"P/E {row['pe_ratio']:.1f}x is {abs(row['pe_vs_sector_pct']):.0f}% {direction} "
            f"the {row['broad_sector']} sector median of {row['sector_pe_median']:.1f}x"
        )

    flagged["rationale"] = flagged.apply(_rationale, axis=1)
    return flagged[["company_id", "company_name", "broad_sector", "valuation_badge", "rationale"]]


def export(db_path: str = DB_PATH, output_dir: str = "output") -> None:
    summary = build_valuation_summary(db_path)
    flags = build_valuation_flags(summary)

    summary.to_excel(f"{output_dir}/valuation_summary.xlsx", index=False)
    flags.to_csv(f"{output_dir}/valuation_flags.csv", index=False)
    print(f"valuation_summary.xlsx: {len(summary)} companies")
    print(f"valuation_flags.csv: {len(flags)} flagged ({(flags['valuation_badge']=='Caution').sum()} Caution, "
          f"{(flags['valuation_badge']=='Discount').sum()} Discount)")


if __name__ == "__main__":
    export()
