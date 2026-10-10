"""Screen 5.2 - Company Profile."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import company_list, load_query
from utils.charts import bar_chart, line_chart

st.title("\U0001F3E2 Company Profile")

companies_df = company_list()
label_map = {f"{row.company_name} ({row.id})": row.id for row in companies_df.itertuples()}
search = st.selectbox("Search by name or ticker", sorted(label_map.keys()))
ticker = label_map[search]

company = load_query("SELECT * FROM companies WHERE id = ?", (ticker,))
sector_row = load_query("SELECT * FROM sectors WHERE company_id = ?", (ticker,))
if company.empty:
    st.error("Company not found.")
    st.stop()

row = company.iloc[0]
st.subheader(f"{row['company_name']} ({ticker})")
if not sector_row.empty:
    st.caption(f"{sector_row.iloc[0]['broad_sector']} \u00b7 {sector_row.iloc[0]['sub_sector']}")
if isinstance(row.get("about_company"), str):
    st.write(row["about_company"])

pl = load_query("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", (ticker,))
bs = load_query("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", (ticker,))
cf = load_query("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", (ticker,))
ratios = load_query("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", (ticker,))

def _fmt(val, suffix="", prefix="", decimals=1):
    if val is None or val != val:  # NaN check without importing pandas here
        return "N/A"
    return f"{prefix}{val:.{decimals}f}{suffix}"

if not ratios.empty:
    latest = ratios.sort_values("year").iloc[-1]
    cols = st.columns(6)
    tiles = [
        ("ROE", _fmt(latest.get("return_on_equity_pct"), suffix="%")),
        ("ROCE", _fmt(latest.get("roce_pct"), suffix="%")),
        ("D/E", _fmt(latest.get("debt_to_equity"), suffix="x", decimals=2)),
        ("NPM", _fmt(latest.get("net_profit_margin_pct"), suffix="%")),
        ("EPS", _fmt(latest.get("earnings_per_share"), prefix="\u20b9")),
        ("FCF (Cr)", _fmt(latest.get("free_cash_flow_cr"), prefix="\u20b9", decimals=0)),
    ]
    for col, (label, value) in zip(cols, tiles):
        col.metric(label, value)
else:
    st.warning("No computed ratios available for this company.")

tab1, tab2, tab3 = st.tabs(["P&L", "Balance Sheet", "Cash Flow"])
with tab1:
    if not pl.empty:
        st.plotly_chart(bar_chart(pl, "year", "sales", "Revenue by Year"), width='stretch')
        st.plotly_chart(bar_chart(pl, "year", "net_profit", "Net Profit by Year"), width='stretch')
        st.dataframe(pl, width='stretch', hide_index=True)
    else:
        st.info("No P&L data available.")
with tab2:
    if not bs.empty:
        st.plotly_chart(bar_chart(bs, "year", "total_assets", "Total Assets by Year"), width='stretch')
        st.dataframe(bs, width='stretch', hide_index=True)
    else:
        st.info("No balance sheet data available.")
with tab3:
    if not cf.empty:
        st.plotly_chart(
            bar_chart(cf, "year", "operating_activity", "Operating Cash Flow by Year"),
            width='stretch',
        )
        st.dataframe(cf, width='stretch', hide_index=True)
    else:
        st.info("No cash flow data available.")

st.markdown("---")
st.caption(
    "Tearsheet PDF export is generated in Sprint 5 (Module 8). "
    "This page pulls live from nifty100.db."
)
