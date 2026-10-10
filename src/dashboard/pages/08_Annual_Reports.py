"""Screen 5.8 - Annual Reports."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import company_list, load_query

st.title("\U0001F4C4 Annual Reports")

companies_df = company_list()
label_map = {f"{row.company_name} ({row.id})": row.id for row in companies_df.itertuples()}
search = st.selectbox("Company", sorted(label_map.keys()))
ticker = label_map[search]

docs = load_query(
    "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC", (ticker,)
)

if docs.empty:
    st.warning(f"No annual report links on file for {ticker}. \u26A0\uFE0F Report unavailable.")
else:
    year_filter = st.selectbox("Filter by year", ["All"] + sorted(docs["year"].unique().tolist(), reverse=True))
    show = docs if year_filter == "All" else docs[docs["year"] == year_filter]

    for _, row in show.iterrows():
        if isinstance(row["annual_report"], str) and row["annual_report"].startswith("http"):
            st.markdown(f"- **{row['year']}**: [Open annual report]({row['annual_report']})")
        else:
            st.markdown(f"- **{row['year']}**: \u26A0\uFE0F Report unavailable")

st.caption(
    "Note: some BSE India report links may return 404 over time (link decay, DQ-13 in the spec). "
    "This page does not re-validate links on every load."
)
