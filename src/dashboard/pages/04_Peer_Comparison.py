"""Screen 5.4 - Peer Comparison."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import load_table, load_query
from utils.charts import radar_chart

st.title("\U0001F465 Peer Comparison")

peer_groups = load_table("peer_groups")
group_names = sorted(peer_groups["peer_group_name"].unique().tolist())
group = st.selectbox("Peer group", group_names)

members = peer_groups[peer_groups["peer_group_name"] == group]
member_ids = members["company_id"].tolist()
benchmark_row = members[members["is_benchmark"] == 1]
benchmark = benchmark_row.iloc[0]["company_id"] if not benchmark_row.empty else member_ids[0]

companies = load_table("companies")[["id", "company_name"]]
member_names = companies[companies["id"].isin(member_ids)]
label_map = {f"{r.company_name} ({r.id})": r.id for r in member_names.itertuples()}

company_label = st.selectbox("Company to inspect", sorted(label_map.keys()))
ticker = label_map[company_label]

percentiles = load_query(
    "SELECT * FROM peer_percentiles WHERE peer_group_name = ? AND company_id = ?",
    (group, ticker),
)

if percentiles.empty:
    st.warning("No peer percentile data for this company/group combination.")
else:
    metrics = percentiles["metric"].unique().tolist()
    latest_year = percentiles["year"].max()
    p_latest = percentiles[percentiles["year"] == latest_year]

    group_all = load_query(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ? AND year = ?",
        (group, latest_year),
    )
    peer_avg = group_all.groupby("metric")["value"].mean()

    cats = p_latest["metric"].tolist()
    company_vals = p_latest["value"].tolist()
    avg_vals = [peer_avg.get(m, 0) for m in cats]

    st.plotly_chart(
        radar_chart(cats, company_vals, avg_vals, ticker, group),
        width='stretch',
    )

    st.subheader("Percentile ranks (0\u20131) within peer group")
    st.dataframe(
        p_latest[["metric", "value", "percentile_rank"]].sort_values("percentile_rank", ascending=False),
        width='stretch', hide_index=True,
    )

st.markdown("---")
st.subheader(f"All members of {group} (benchmark: {benchmark})")
st.dataframe(member_names.rename(columns={"id": "ticker"}), width='stretch', hide_index=True)
