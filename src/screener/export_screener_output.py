"""
Sprint 3, Day 17: Generate output/screener_output.xlsx — one sheet per preset,
20 KPI columns, sorted by composite score descending, green/red colour-coded
cells for meeting/failing each preset's own threshold columns.
"""

import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import PatternFill

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src" / "screener"))

from engine import build_universe, load_config
from presets import run_all_presets
from composite_score import compute_composite_score

import sqlite3

GREEN = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
RED = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

DISPLAY_COLS = [
    "company_id", "company_name", "broad_sector",
    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct",
    "debt_to_equity", "interest_coverage", "icr_label",
    "asset_turnover", "free_cash_flow_cr", "capex_cr",
    "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
    "pe_ratio", "pb_ratio", "dividend_yield_pct", "fcf_yield_pct",
    "composite_quality_score",
]

# threshold column -> (preset filter key, comparison) for colour-coding
PRESET_THRESHOLD_COLS = {
    "Quality Compounder": {"return_on_equity_pct": (">=", 15), "debt_to_equity": ("<=", 1.0), "revenue_cagr_5yr": (">=", 10)},
    "Value Pick": {"pe_ratio": ("<=", 36), "pb_ratio": ("<=", 6.5), "dividend_yield_pct": (">=", 1)},
    "Growth Accelerator": {"pat_cagr_5yr": (">=", 20), "revenue_cagr_5yr": (">=", 15)},
    "Dividend Champion": {"dividend_yield_pct": (">=", 2)},
    "Debt-Free Blue Chip": {"debt_to_equity": ("<=", 0), "return_on_equity_pct": (">=", 12)},
    "Turnaround Watch": {"revenue_cagr_5yr": (">=", 10)},
}


def _colour_sheet(ws, df, threshold_cols):
    header = [c.value for c in ws[1]]
    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        for col_name, (op, threshold) in threshold_cols.items():
            if col_name not in header:
                continue
            col_idx = header.index(col_name) + 1
            value = row.get(col_name)
            if pd.isna(value):
                continue
            passes = (value >= threshold) if op == ">=" else (value <= threshold)
            ws.cell(row=row_idx, column=col_idx).fill = GREEN if passes else RED


def main():
    conn = sqlite3.connect(BASE_DIR / "data" / "nifty100.db")
    universe = build_universe(conn)
    conn.close()

    # recompute composite score with the full Day 17 weighting
    universe = compute_composite_score(universe)

    presets = run_all_presets()

    output_path = BASE_DIR / "output" / "screener_output.xlsx"
    output_path.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for name, df in presets.items():
            # re-merge with the refreshed composite score
            df = df.drop(columns=["composite_quality_score"], errors="ignore").merge(
                universe[["company_id", "composite_quality_score"]], on="company_id", how="left"
            )
            df = df.sort_values("composite_quality_score", ascending=False)
            cols = [c for c in DISPLAY_COLS if c in df.columns]
            sheet_df = df[cols]
            sheet_name = name[:31]  # Excel sheet name limit
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    # re-open to apply colour coding
    from openpyxl import load_workbook
    wb = load_workbook(output_path)
    for name, df in presets.items():
        sheet_name = name[:31]
        if sheet_name not in wb.sheetnames:
            continue
        df = df.merge(universe[["company_id", "composite_quality_score"]].drop_duplicates(),
                       on="company_id", how="left", suffixes=("", "_new"))
        df = df.sort_values("composite_quality_score" if "composite_quality_score" in df.columns else "composite_quality_score_new",
                             ascending=False)
        threshold_cols = PRESET_THRESHOLD_COLS.get(name, {})
        _colour_sheet(wb[sheet_name], df, threshold_cols)
    wb.save(output_path)

    print(f"screener_output.xlsx written: {output_path}")
    print(f"Sheets: {list(presets.keys())}")
    for name, df in presets.items():
        print(f"  {name}: {len(df)} companies")


if __name__ == "__main__":
    main()
