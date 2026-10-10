"""Screen 5.6 - Sector Analysis."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import load_table, latest_ratios
from utils.charts import bubble_chart, bar_chart

st.title("\U0001F3ED Sector Analysis")

sectors = load_table("sectors")
ratios = latest_ratios()
market_cap = load_table("market_cap")
mc_latest = market_cap[market_cap["year"] == market_cap["year"].max()]
companies = load_table("companies")[["id", "company_name"]]

sector_choice = st.selectbox("Sector", sorted(sectors["broad_sector"].dropna().unique().tolist()))

merged = ratios.merge(sectors, on="company_id", how="left")
merged = merged.merge(mc_latest[["company_id", "market_cap_crore"]], on="company_id", how="left")
merged = merged.merge(companies, left_on="company_id", right_on="id", how="left")
pl = load_table("profitandloss")
pl_latest = pl.sort_values("year").groupby("company_id").tail(1)[["company_id", "sales"]]
merged = merged.merge(pl_latest, on="company_id", how="left")

sector_df = merged[merged["broad_sector"] == sector_choice].dropna(subset=["market_cap_crore"])

if sector_df.empty:
    st.warning("No market-cap-linked data available for this sector.")
else:
    st.plotly_chart(
        bubble_chart(
            sector_df, "sales", "return_on_equity_pct", "market_cap_crore", "sub_sector",
            "company_name", f"{sector_choice}: Revenue vs ROE (bubble = market cap)",
        ),
        width='stretch',
    )

st.markdown("---")
st.subheader(f"{sector_choice} \u2014 median KPIs")
sector_kpis = merged[merged["broad_sector"] == sector_choice][
    ["return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct", "roce_pct"]
].median().reset_index()
sector_kpis.columns = ["metric", "median_value"]
st.plotly_chart(bar_chart(sector_kpis, "metric", "median_value", "Sector Median KPIs"), width='stretch')

st.markdown("---")
st.subheader(f"All companies in {sector_choice}")
st.dataframe(
    merged[merged["broad_sector"] == sector_choice][
        ["company_id", "company_name", "sub_sector", "return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct"]
    ].sort_values("return_on_equity_pct", ascending=False, na_position="last"),
    width='stretch', hide_index=True,
)
