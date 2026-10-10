"""Screen 5.7 - Capital Allocation Map."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import load_table
from utils.charts import bar_chart

st.title("\U0001F5FA\uFE0F Capital Allocation Map")

CSV_PATH = Path(__file__).resolve().parents[3] / "output" / "capital_allocation.csv"

if not CSV_PATH.exists():
    st.error("capital_allocation.csv not found. Run src/analytics/cashflow_kpis.py first.")
    st.stop()

ca = pd.read_csv(CSV_PATH)
years = sorted(ca["year"].dropna().unique().tolist())
year = st.select_slider("Year", options=years, value=years[-1])

year_df = ca[ca["year"] == year]
pattern_counts = year_df["pattern_label"].value_counts().reset_index()
pattern_counts.columns = ["pattern_label", "count"]

st.plotly_chart(
    bar_chart(pattern_counts, "pattern_label", "count", f"Capital Allocation Patterns \u2014 {year}"),
    width='stretch',
)

st.markdown("---")
pattern_choice = st.selectbox("Click a pattern to see the company list", pattern_counts["pattern_label"].tolist())

companies = load_table("companies")[["id", "company_name"]]
detail = year_df[year_df["pattern_label"] == pattern_choice].merge(
    companies, left_on="company_id", right_on="id", how="left"
)
st.subheader(f"{pattern_choice} \u2014 {len(detail)} companies ({year})")
st.dataframe(
    detail[["company_id", "company_name", "cfo_sign", "cfi_sign", "cff_sign"]],
    width='stretch', hide_index=True,
)

csv = ca.to_csv(index=False).encode("utf-8")
st.download_button("\U0001F4E5 Download full capital allocation history", csv, "capital_allocation.csv", "text/csv")
