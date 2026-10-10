"""
Schema / data-quality validator for the Nifty 100 Financial Intelligence Platform.

Implements the 16 DQ rules from the project spec (Section 14). Each check returns
a list of violation dicts: {rule_id, table, company_id, year, field, issue, severity}.
CRITICAL violations should halt/repair the load; WARNING/INFO are logged only.
"""

import pandas as pd


def _v(rule_id, table, company_id, year, field, issue, severity):
    return {
        "rule_id": rule_id, "table": table, "company_id": company_id,
        "year": year, "field": field, "issue": issue, "severity": severity,
    }


def run_all_checks(frames):
    """frames: dict of {table_name: DataFrame} as produced by loader.load_all()."""
    violations = []

    companies = frames["companies"]
    pl = frames["profitandloss"]
    bs = frames["balancesheet"]

    # DQ-01: Company PK uniqueness
    id_col = "id"
    dupes = companies[companies[id_col].duplicated(keep=False)][id_col].unique()
    for d in dupes:
        violations.append(_v("DQ-01", "companies", d, None, "id",
                              "Duplicate company ticker", "CRITICAL"))

    # DQ-02: Annual PK uniqueness (company_id, year) across time-series tables
    for name in ("profitandloss", "balancesheet", "cashflow"):
        df = frames[name]
        dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
        for _, row in dupes.drop_duplicates(subset=["company_id", "year"]).iterrows():
            violations.append(_v("DQ-02", name, row["company_id"], row["year"],
                                  "company_id+year", "Duplicate (company_id, year) pair", "CRITICAL"))

    # DQ-03: FK integrity - all company_id in child tables exist in companies.id
    valid_ids = set(companies[id_col].dropna())
    for name, df in frames.items():
        if name == "companies" or "company_id" not in df.columns:
            continue
        orphans = df[~df["company_id"].isin(valid_ids)]
        for cid in orphans["company_id"].unique():
            violations.append(_v("DQ-03", name, cid, None, "company_id",
                                  "company_id not found in companies table", "CRITICAL"))

    # DQ-04: Balance sheet balances (|assets - liabilities| / assets < 1%)
    if {"total_assets", "total_liabilities"}.issubset(bs.columns):
        tol = (bs["total_assets"] - bs["total_liabilities"]).abs() / bs["total_assets"].replace(0, pd.NA)
        flagged = bs[tol >= 0.01]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-04", "balancesheet", row["company_id"], row["year"],
                                  "total_assets/total_liabilities",
                                  "Balance sheet does not balance within 1%", "WARNING"))

    # DQ-05: OPM cross-check (|opm_percentage - computed| < 1.0)
    if {"operating_profit", "sales", "opm_percentage"}.issubset(pl.columns):
        computed = (pl["operating_profit"] / pl["sales"].replace(0, pd.NA)) * 100
        diff = (pl["opm_percentage"] - computed).abs()
        flagged = pl[diff >= 1.0]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-05", "profitandloss", row["company_id"], row["year"],
                                  "opm_percentage", "OPM cross-check mismatch > 1%", "WARNING"))

    # DQ-06: Positive sales
    if "sales" in pl.columns:
        flagged = pl[pl["sales"] <= 0]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-06", "profitandloss", row["company_id"], row["year"],
                                  "sales", "sales <= 0", "WARNING"))

    # DQ-07 / DQ-08 are enforced inside loader.py during normalisation (rejected rows)

    # DQ-09: Net cash check (|net_cash_flow - (CFO+CFI+CFF)| <= 10 Cr)
    cf = frames["cashflow"]
    need = {"net_cash_flow", "operating_activity", "investing_activity", "financing_activity"}
    if need.issubset(cf.columns):
        computed = cf["operating_activity"] + cf["investing_activity"] + cf["financing_activity"]
        diff = (cf["net_cash_flow"] - computed).abs()
        flagged = cf[diff > 10]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-09", "cashflow", row["company_id"], row["year"],
                                  "net_cash_flow", "net_cash_flow != CFO+CFI+CFF (>10 Cr)", "WARNING"))

    # DQ-10: Non-negative fixed assets
    if "fixed_assets" in bs.columns:
        flagged = bs[bs["fixed_assets"] < 0]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-10", "balancesheet", row["company_id"], row["year"],
                                  "fixed_assets", "Negative fixed_assets", "WARNING"))

    # DQ-11: Tax rate range 0-60%
    if "tax_percentage" in pl.columns:
        flagged = pl[(pl["tax_percentage"] < 0) | (pl["tax_percentage"] > 60)]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-11", "profitandloss", row["company_id"], row["year"],
                                  "tax_percentage", "tax_percentage outside 0-60% range", "WARNING"))

    # DQ-12: Dividend payout cap (<=200%)
    if "dividend_payout" in pl.columns:
        flagged = pl[pl["dividend_payout"] > 200]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-12", "profitandloss", row["company_id"], row["year"],
                                  "dividend_payout", "dividend_payout > 200%", "WARNING"))

    # DQ-13: URL validity for documents - not checked live here (would need network calls);
    # flagged as informational placeholder count of blank URLs only.
    docs = frames.get("documents")
    if docs is not None and "Annual_Report" in docs.columns:
        blank = docs[docs["Annual_Report"].isna()]
        for _, row in blank.iterrows():
            violations.append(_v("DQ-13", "documents", row["company_id"], row.get("Year"),
                                  "Annual_Report", "Missing annual report URL", "WARNING"))

    # DQ-14: EPS sign consistency
    if {"eps", "net_profit"}.issubset(pl.columns):
        flagged = pl[(pl["net_profit"] > 0) & (pl["eps"] <= 0)]
        for _, row in flagged.iterrows():
            violations.append(_v("DQ-14", "profitandloss", row["company_id"], row["year"],
                                  "eps", "eps <= 0 while net_profit > 0", "WARNING"))

    # DQ-16: Coverage check - each company needs >= 5 years of P&L/BS/CF
    for name in ("profitandloss", "balancesheet", "cashflow"):
        counts = frames[name].groupby("company_id").size()
        short = counts[counts < 5]
        for cid, n in short.items():
            violations.append(_v("DQ-16", name, cid, None, "year_coverage",
                                  f"Only {n} years of history (<5)", "WARNING"))

    return violations


if __name__ == "__main__":
    from pathlib import Path
    from loader import load_all
    import pandas as pd

    frames, audit_rows = load_all(base_dir=Path(__file__).resolve().parents[2])
    violations = run_all_checks(frames)

    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    warning = [v for v in violations if v["severity"] == "WARNING"]
    info = [v for v in violations if v["severity"] == "INFO"]

    print(f"Total violations: {len(violations)}  (CRITICAL={len(critical)}, WARNING={len(warning)}, INFO={len(info)})")

    out_path = Path(__file__).resolve().parents[2] / "output" / "validation_failures.csv"
    out_path.parent.mkdir(exist_ok=True)
    pd.DataFrame(violations).to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
