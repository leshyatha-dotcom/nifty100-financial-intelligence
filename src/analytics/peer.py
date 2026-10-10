"""
Sprint 3, Day 18: Peer Comparison Engine.

Computes PERCENT_RANK for 10 metrics within each of the 11 peer groups
(from peer_groups.xlsx), using each company's latest-year financial_ratios
row. D/E is inverted (1 - percentile) so that lower D/E ranks higher.
Populates the `peer_percentiles` table in SQLite.

Companies not in any peer group return "No peer group assigned" - handled
gracefully in get_company_peer_data(), no exception raised.
"""

from pathlib import Path
import sqlite3

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"

METRICS = [
    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity",
    "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr",
    "interest_coverage", "asset_turnover",
]

INVERT_METRICS = {"debt_to_equity"}  # lower is better -> invert percentile


def build_peer_percentiles(conn):
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)

    fr_latest = fr.sort_values("year").groupby("company_id").tail(1)
    merged = peer_groups.merge(fr_latest, on="company_id", how="left")

    rows = []
    for group_name, g in merged.groupby("peer_group_name"):
        for metric in METRICS:
            if metric not in g.columns:
                continue
            pct = g[metric].rank(pct=True, na_option="keep")
            if metric in INVERT_METRICS:
                pct = 1 - pct
            for company_id, value, rank in zip(g["company_id"], g[metric], pct):
                rows.append({
                    "company_id": company_id,
                    "peer_group_name": group_name,
                    "metric": metric,
                    "value": value,
                    "percentile_rank": round(rank, 4) if pd.notna(rank) else None,
                    "year": g["year"].iloc[0] if "year" in g.columns else None,
                })

    return pd.DataFrame(rows)


def create_peer_percentiles_table(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS peer_percentiles;
        CREATE TABLE peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year TEXT,
            PRIMARY KEY (company_id, peer_group_name, metric)
        );
    """)


def get_company_peer_data(conn, company_id):
    """Returns peer percentile rows for a company, or a friendly message if it's in no group."""
    df = pd.read_sql(
        "SELECT * FROM peer_percentiles WHERE company_id = ?", conn, params=(company_id,)
    )
    if df.empty:
        return "No peer group assigned"
    return df


def main():
    conn = sqlite3.connect(DB_PATH)
    create_peer_percentiles_table(conn)

    percentiles_df = build_peer_percentiles(conn)
    percentiles_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()

    n_groups = conn.execute("SELECT COUNT(DISTINCT peer_group_name) FROM peer_percentiles").fetchone()[0]
    n_rows = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    conn.close()

    print(f"peer_percentiles table populated: {n_rows} rows across {n_groups} peer groups")
    return n_groups


if __name__ == "__main__":
    main()
