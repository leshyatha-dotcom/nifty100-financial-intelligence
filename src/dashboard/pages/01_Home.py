"""Screen 5.1 - Home / Overview."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import load_table, latest_ratios
from utils.charts import donut_chart, bar_chart

st.title("\U0001F3E0 Home / Overview")

companies = load_table("companies")
sectors = load_table("sectors")
ratios = latest_ratios()

sector_options = ["All"] + sorted(sectors["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Filter by sector", sector_options)

merged = ratios.merge(sectors, on="company_id", how="left")
if selected_sector != "All":
    merged = merged[merged["broad_sector"] == selected_sector]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Companies", f"{merged['company_id'].nunique()}")
col2.metric("Avg ROE", f"{merged['return_on_equity_pct'].mean():.1f}%" if not merged.empty else "N/A")
col3.metric("Avg D/E", f"{merged['debt_to_equity'].mean():.2f}x" if not merged.empty else "N/A")
col4.metric("Avg NPM", f"{merged['net_profit_margin_pct'].mean():.1f}%" if not merged.empty else "N/A")

market_cap = load_table("market_cap")
latest_year = market_cap["year"].max()
mc_latest = market_cap[market_cap["year"] == latest_year]
median_pe = mc_latest["pe_ratio"].median()
st.caption(f"Median P/E across the universe (FY{latest_year}): **{median_pe:.1f}x** \u00b7 "
           "Simulated valuation data.")

st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    sector_counts = sectors["broad_sector"].value_counts().reset_index()
    sector_counts.columns = ["broad_sector", "count"]
    st.plotly_chart(
        donut_chart(sector_counts, "broad_sector", "count", "Companies by Sector"),
        width='stretch',
    )
with c2:
    sector_roe = merged.groupby("broad_sector", dropna=True)["return_on_equity_pct"].median().reset_index()
    sector_roe = sector_roe.sort_values("return_on_equity_pct", ascending=False)
    st.plotly_chart(
        bar_chart(sector_roe, "broad_sector", "return_on_equity_pct", "Median ROE by Sector"),
        width='stretch',
    )

st.markdown("---")
st.subheader("Market health banner")
avg_de = merged["debt_to_equity"].mean()
if avg_de is not None and avg_de < 1.0:
    st.success("Universe leverage is healthy on average (D/E < 1.0).")
else:
    st.warning("Average leverage across the current filter is elevated (D/E \u2265 1.0).")
