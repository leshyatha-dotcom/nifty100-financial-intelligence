"""
Sprint 2, Day 12: run the full ratio + CAGR + cash-flow-KPI engine across all
92 companies x all available years and populate the `financial_ratios` table.

Also emits (Day 11 / Day 13 deliverables):
  - output/capital_allocation.csv
  - output/ratio_edge_cases.log
"""

import sys
from pathlib import Path

import pandas as pd
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src" / "analytics"))

from ratios import (
    net_profit_margin, operating_profit_margin, opm_cross_check,
    return_on_equity, return_on_capital_employed, return_on_assets,
    debt_to_equity, high_leverage_flag, interest_coverage, icr_label,
    icr_warning_flag, net_debt, asset_turnover,
)
from cagr import cagr
from cashflow_kpis import (
    free_cash_flow, cfo_quality_score, capex_intensity, fcf_conversion_rate,
    capex_cr as capex_cr_fn, capital_allocation_pattern,
)

DB_PATH = BASE_DIR / "data" / "nifty100.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
OUTPUT_DIR = BASE_DIR / "output"


def load_tables(conn):
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id FROM companies", conn)
    return pl, bs, cf, sectors, companies


def compute_all(pl, bs, cf, sectors):
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    rows = []
    capital_alloc_rows = []
    edge_cases = []

    companies_list = sorted(set(pl["company_id"]) & set(bs["company_id"]) & set(cf["company_id"]))

    for cid in companies_list:
        pl_c = pl[pl["company_id"] == cid].sort_values("year").reset_index(drop=True)
        bs_c = bs[bs["company_id"] == cid].set_index("year")
        cf_c = cf[cf["company_id"] == cid].set_index("year")
        sector = sector_map.get(cid)

        sales_series = dict(zip(pl_c["year"], pl_c["sales"]))
        pat_series = dict(zip(pl_c["year"], pl_c["net_profit"]))
        eps_series = dict(zip(pl_c["year"], pl_c["eps"]))

        cfo_hist, pat_hist = [], []

        for _, pl_row in pl_c.iterrows():
            year = pl_row["year"]
            if year not in bs_c.index or year not in cf_c.index:
                continue
            bs_row = bs_c.loc[year]
            cf_row = cf_c.loc[year]

            sales = pl_row["sales"]
            net_profit = pl_row["net_profit"]
            operating_profit = pl_row["operating_profit"]
            depreciation = pl_row["depreciation"]
            other_income = pl_row["other_income"]
            interest = pl_row["interest"]
            eps = pl_row["eps"]
            dividend_payout = pl_row["dividend_payout"]

            equity_capital = bs_row["equity_capital"]
            reserves = bs_row["reserves"]
            borrowings = bs_row["borrowings"]
            total_assets = bs_row["total_assets"]
            investments = bs_row["investments"]

            cfo = cf_row["operating_activity"]
            cfi = cf_row["investing_activity"]
            cff = cf_row["financing_activity"]

            npm = net_profit_margin(net_profit, sales)
            opm_computed = operating_profit_margin(operating_profit, sales)
            if opm_cross_check(opm_computed, pl_row.get("opm_percentage")):
                edge_cases.append(f"{cid} {year}: OPM cross-check mismatch "
                                   f"(computed={opm_computed}, source={pl_row.get('opm_percentage')})")

            roe = return_on_equity(net_profit, equity_capital, reserves)
            roce = return_on_capital_employed(operating_profit, depreciation, equity_capital, reserves, borrowings)
            roa = return_on_assets(net_profit, total_assets)

            de = debt_to_equity(borrowings, equity_capital, reserves)
            hl_flag = high_leverage_flag(de, sector)
            icr = interest_coverage(operating_profit, other_income, interest)
            icr_lbl = icr_label(icr)
            icr_warn = icr_warning_flag(icr)
            nd = net_debt(borrowings, investments)
            at = asset_turnover(sales, total_assets)

            fcf = free_cash_flow(cfo, cfi)
            capex = capex_cr_fn(cfi)
            capex_pct, capex_lbl = capex_intensity(cfi, sales)
            fcf_conv = fcf_conversion_rate(fcf, operating_profit)

            cfo_hist.append(cfo)
            pat_hist.append(net_profit)
            if len(cfo_hist) > 5:
                cfo_hist.pop(0)
                pat_hist.pop(0)
            cfo_q_score, cfo_q_label = cfo_quality_score(cfo_hist, pat_hist)

            cfo_s, cfi_s, cff_s, pattern_label = capital_allocation_pattern(cfo, cfi, cff, cfo_q_score)
            capital_alloc_rows.append({
                "company_id": cid, "year": year, "cfo_sign": cfo_s,
                "cfi_sign": cfi_s, "cff_sign": cff_s, "pattern_label": pattern_label,
            })

            rev_cagr, rev_flag = _lookback_cagr(sales_series, year, 5)
            if rev_flag == "TURNAROUND":
                edge_cases.append(f"{cid} {year}: revenue CAGR TURNAROUND (base<0, end>0)")
            pat_cagr_v, pat_flag = _lookback_cagr(pat_series, year, 5)
            if pat_flag == "TURNAROUND":
                edge_cases.append(f"{cid} {year}: PAT CAGR TURNAROUND (base<0, end>0)")
            eps_cagr_v, eps_flag = _lookback_cagr(eps_series, year, 5)

            rows.append({
                "company_id": cid, "year": year,
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm_computed,
                "return_on_equity_pct": roe,
                "debt_to_equity": de,
                "interest_coverage": icr,
                "asset_turnover": at,
                "free_cash_flow_cr": fcf,
                "capex_cr": capex,
                "earnings_per_share": eps,
                "book_value_per_share": None,
                "dividend_payout_ratio_pct": dividend_payout,
                "total_debt_cr": borrowings,
                "cash_from_operations_cr": cfo,
                "roce_pct": roce,
                "roa_pct": roa,
                "high_leverage_flag": int(hl_flag),
                "icr_label": icr_lbl,
                "icr_warning_flag": int(icr_warn),
                "net_debt_cr": nd,
                "revenue_cagr_5yr": rev_cagr,
                "revenue_cagr_5yr_flag": rev_flag,
                "pat_cagr_5yr": pat_cagr_v,
                "pat_cagr_5yr_flag": pat_flag,
                "eps_cagr_5yr": eps_cagr_v,
                "eps_cagr_5yr_flag": eps_flag,
                "cfo_quality_score": cfo_q_score,
                "cfo_quality_label": cfo_q_label,
                "capex_intensity_pct": capex_pct,
                "capex_intensity_label": capex_lbl,
                "fcf_conversion_pct": fcf_conv,
                "composite_quality_score": None,
            })

    df = pd.DataFrame(rows)
    df = _add_composite_quality_score(df)
    return df, pd.DataFrame(capital_alloc_rows), edge_cases


def _lookback_cagr(series, current_year, n_years):
    cur_yr_num = int(str(current_year)[:4])
    base_yr_num = cur_yr_num - n_years
    base_key = next((k for k in series if str(k)[:4] == str(base_yr_num)), None)
    if base_key is None or current_year not in series:
        return None, "INSUFFICIENT"
    return cagr(series[base_key], series[current_year], n_years)


def _winsorised_score(series, p10, p90):
    clipped = series.clip(lower=p10, upper=p90)
    if p90 == p10:
        return pd.Series([50.0] * len(series), index=series.index)
    return (clipped - p10) / (p90 - p10) * 100


def _add_composite_quality_score(df):
    roe = df["return_on_equity_pct"]
    roce = df["roce_pct"]
    fcf = df["free_cash_flow_cr"]
    de = df["debt_to_equity"]

    roe_score = _winsorised_score(roe, roe.quantile(0.10), roe.quantile(0.90))
    roce_score = _winsorised_score(roce, roce.quantile(0.10), roce.quantile(0.90))
    fcf_score = _winsorised_score(fcf, fcf.quantile(0.10), fcf.quantile(0.90))
    de_score = 100 - _winsorised_score(de, de.quantile(0.10), de.quantile(0.90))

    composite = (
        0.30 * roe_score.fillna(0)
        + 0.25 * fcf_score.fillna(0)
        + 0.25 * roce_score.fillna(0)
        + 0.20 * de_score.fillna(0)
    )
    df["composite_quality_score"] = composite.round(1)
    return df


def main():
    conn = sqlite3.connect(DB_PATH)
    pl, bs, cf, sectors, companies = load_tables(conn)

    ratios_df, capital_alloc_df, edge_cases = compute_all(pl, bs, cf, sectors)

    conn.executescript(
        "DROP TABLE IF EXISTS financial_ratios;\n"
        + [s for s in SCHEMA_PATH.read_text().split(";\n\n")
           if "CREATE TABLE financial_ratios" in s][0] + ";"
    )
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    row_count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    conn.close()

    OUTPUT_DIR.mkdir(exist_ok=True)
    capital_alloc_df.to_csv(OUTPUT_DIR / "capital_allocation.csv", index=False)
    with open(OUTPUT_DIR / "ratio_edge_cases.log", "w") as f:
        f.write(f"Ratio Engine Edge Case Log - {len(edge_cases)} entries\n")
        f.write("=" * 60 + "\n")
        for line in edge_cases:
            f.write(line + "\n")

    print(f"financial_ratios rows written: {row_count}")
    print(f"capital_allocation.csv rows: {len(capital_alloc_df)}")
    print(f"ratio_edge_cases.log entries: {len(edge_cases)}")
    return row_count


if __name__ == "__main__":
    main()
