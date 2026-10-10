"""
Sprint 3, Day 19: Radar charts.

8 axes: ROE, ROCE, NPM, D/E (inverted so lower=better shows outward), FCF score
(binary positive/negative scaled), PAT CAGR 5yr, Revenue CAGR 5yr, Composite Score.

Each chart: company's values as a filled polygon, peer group average as a dashed
outline overlay. Companies with no peer group get a standalone chart with the
Nifty 100 average as the reference line instead.
"""

from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"
OUT_DIR = BASE_DIR / "reports" / "radar_charts"

AXES = ["ROE", "ROCE", "NPM", "D/E (inv)", "FCF+", "PAT CAGR 5yr", "Rev CAGR 5yr", "Composite"]

RAW_COLS = [
    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity",
    "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score",
]


def _scale_row(row, bounds):
    """Scale a company's 8 raw metrics to 0-100 using universe P10/P90 bounds. D/E inverted, FCF binary."""
    values = []
    for col in RAW_COLS:
        v = row.get(col)
        if col == "debt_to_equity":
            p10, p90 = bounds[col]
            if pd.isna(v) or p90 == p10:
                values.append(50.0)
            else:
                clipped = min(max(v, p10), p90)
                values.append(100 - (clipped - p10) / (p90 - p10) * 100)
        elif col == "free_cash_flow_cr":
            values.append(100.0 if (pd.notna(v) and v > 0) else 0.0)
        else:
            p10, p90 = bounds[col]
            if pd.isna(v) or p90 == p10:
                values.append(50.0)
            else:
                clipped = min(max(v, p10), p90)
                values.append((clipped - p10) / (p90 - p10) * 100)
    return values


def _plot_radar(company_id, company_values, overlay_values, overlay_label, out_path):
    angles = np.linspace(0, 2 * np.pi, len(AXES), endpoint=False).tolist()
    company_values = company_values + company_values[:1]
    overlay_values = overlay_values + overlay_values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, company_values, color="#1f77b4", linewidth=2)
    ax.fill(angles, company_values, color="#1f77b4", alpha=0.25)
    ax.plot(angles, overlay_values, color="#d62728", linewidth=1.5, linestyle="--", label=overlay_label)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXES, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title(company_id, fontsize=13, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main():
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()

    fr_latest = fr.sort_values("year").groupby("company_id").tail(1).set_index("company_id")

    bounds = {col: (fr_latest[col].quantile(0.10), fr_latest[col].quantile(0.90)) for col in RAW_COLS}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0

    for company_id, row in fr_latest.iterrows():
        company_values = _scale_row(row, bounds)

        groups = peer_groups[peer_groups["company_id"] == company_id]["peer_group_name"].tolist()
        if groups:
            group_name = groups[0]
            peers = peer_groups[peer_groups["peer_group_name"] == group_name]["company_id"].tolist()
            peer_rows = fr_latest.loc[fr_latest.index.intersection(peers)]
            overlay_values = [np.mean([_scale_row(peer_rows.loc[p], bounds)[i] for p in peer_rows.index])
                               for i in range(len(RAW_COLS))]
            overlay_label = f"{group_name} avg"
        else:
            overlay_values = [np.mean([_scale_row(fr_latest.loc[c], bounds)[i] for c in fr_latest.index])
                               for i in range(len(RAW_COLS))]
            overlay_label = "Nifty 100 avg"

        out_path = OUT_DIR / f"{company_id}_radar.png"
        _plot_radar(company_id, company_values, overlay_values, overlay_label, out_path)
        generated += 1

    print(f"Radar charts generated: {generated} -> {OUT_DIR}")
    return generated


if __name__ == "__main__":
    main()
