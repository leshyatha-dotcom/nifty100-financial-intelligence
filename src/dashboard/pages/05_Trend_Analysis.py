"""Screen 5.5 - Trend Analysis."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import company_list, load_query
from utils.charts import line_chart

st.title("\U0001F4C8 Trend Analysis")

companies_df = company_list()
label_map = {f"{row.company_name} ({row.id})": row.id for row in companies_df.itertuples()}
search = st.selectbox("Company", sorted(label_map.keys()))
ticker = label_map[search]

METRIC_OPTIONS = {
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "ROE (%)": "return_on_equity_pct",
    "ROCE (%)": "roce_pct",
    "Debt-to-Equity": "debt_to_equity",
    "Free Cash Flow (Cr)": "free_cash_flow_cr",
    "EPS": "earnings_per_share",
}
selected_labels = st.multiselect(
    "Metrics to overlay (up to 3)", list(METRIC_OPTIONS.keys()),
    default=["ROE (%)"], max_selections=3,
)

ratios = load_query(
    "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", (ticker,)
)

if ratios.empty:
    st.warning("No ratio history available for this company.")
elif not selected_labels:
    st.info("Select at least one metric to plot.")
else:
    for label in selected_labels:
        col = METRIC_OPTIONS[label]
        if col not in ratios.columns:
            continue
        chart_df = ratios[["year", col]].dropna()
        st.plotly_chart(line_chart(chart_df, "year", col, f"{label} \u2014 {ticker}"), width='stretch')

        chart_df = chart_df.reset_index(drop=True)
        if len(chart_df) >= 2:
            latest_val = chart_df[col].iloc[-1]
            prev_val = chart_df[col].iloc[-2]
            if prev_val not in (0, None) and prev_val == prev_val:
                yoy = (latest_val - prev_val) / abs(prev_val) * 100
                direction = "\u2191" if yoy > 0 else ("\u2193" if yoy < 0 else "\u2192")
                st.caption(f"YoY change (latest vs prior year): {direction} {yoy:+.1f}%")

    csv = ratios.to_csv(index=False).encode("utf-8")
    st.download_button("\U0001F4E5 Download full ratio history as CSV", csv, f"{ticker}_ratios.csv", "text/csv")
