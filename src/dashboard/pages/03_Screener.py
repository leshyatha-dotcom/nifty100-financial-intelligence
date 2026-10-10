"""Screen 5.3 - Financial Screener."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import load_table, latest_ratios

st.title("\U0001F50D Financial Screener")

ratios = latest_ratios()
sectors = load_table("sectors")
market_cap = load_table("market_cap")
mc_latest = market_cap[market_cap["year"] == market_cap["year"].max()]

df = ratios.merge(sectors, on="company_id", how="left")
df = df.merge(mc_latest[["company_id", "pe_ratio", "pb_ratio", "dividend_yield_pct"]], on="company_id", how="left")
df = df.merge(load_table("companies")[["id", "company_name"]], left_on="company_id", right_on="id", how="left")

PRESETS = {
    "Custom": None,
    "Quality Compounder": dict(min_roe=15, max_de=1.0, min_fcf=0),
    "Value Pick": dict(max_pe=36, max_pb=6.5),
    "Debt-Free Blue Chip": dict(max_de=0.0, min_roe=12),
}

st.sidebar.header("Screener Filters")
preset_name = st.sidebar.selectbox("Preset", list(PRESETS.keys()))

sector_filter = st.sidebar.selectbox(
    "Sector", ["All"] + sorted(sectors["broad_sector"].dropna().unique().tolist())
)

preset = PRESETS.get(preset_name)
min_roe = st.sidebar.slider("Min ROE (%)", -20, 60, preset.get("min_roe", -20) if preset else -20)
max_de = st.sidebar.slider("Max D/E", 0.0, 10.0, float(preset.get("max_de", 10.0)) if preset else 10.0, 0.1)
min_fcf = st.sidebar.slider("Min FCF (Cr)", -5000, 5000, preset.get("min_fcf", -5000) if preset else -5000)
max_pe = st.sidebar.slider("Max P/E", 0, 100, preset.get("max_pe", 100) if preset else 100)
min_npm = st.sidebar.slider("Min Net Profit Margin (%)", -50, 60, -50)

filtered = df.copy()
if sector_filter != "All":
    filtered = filtered[filtered["broad_sector"] == sector_filter]

filtered = filtered[
    (filtered["return_on_equity_pct"].fillna(-999) >= min_roe)
    & (filtered["debt_to_equity"].fillna(999) <= max_de)
    & (filtered["free_cash_flow_cr"].fillna(-999999) >= min_fcf)
    & (filtered["pe_ratio"].fillna(0) <= max_pe)
    & (filtered["net_profit_margin_pct"].fillna(-999) >= min_npm)
]

st.write(f"**{len(filtered)} companies** match the current filters.")

display_cols = [
    "company_id", "company_name", "broad_sector",
    "return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct",
    "free_cash_flow_cr", "pe_ratio", "pb_ratio", "dividend_yield_pct",
    "composite_quality_score",
]
display_cols = [c for c in display_cols if c in filtered.columns]
st.dataframe(
    filtered[display_cols].sort_values("composite_quality_score", ascending=False, na_position="last"),
    width='stretch', hide_index=True,
)

csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("\U0001F4E5 Download results as CSV", csv, "screener_results.csv", "text/csv")
