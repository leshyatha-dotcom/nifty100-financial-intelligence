"""
Sprint 5 - NLP Pros/Cons Generator
Aggregates existing pros/cons text per company and auto-generates
additional data-driven insights from financial ratios.
"""

import sqlite3
import os


def get_connection(db_path="data/nifty100.db"):
    return sqlite3.connect(db_path)


def aggregate_pros_cons(conn, company_id):
    """Combine all pros/cons rows for a company into clean lists."""
    rows = conn.execute(
        "SELECT pros, cons FROM prosandcons WHERE company_id = ?",
        (company_id,)
    ).fetchall()

    pros = [r[0] for r in rows if r[0]]
    cons = [r[1] for r in rows if r[1]]
    return pros, cons


def generate_ratio_insights(conn, company_id):
    """
    Auto-generate additional pros/cons style insights from
    financial_ratios table using simple rule-based thresholds.
    """
    insights_pros = []
    insights_cons = []

    row = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
        (company_id,)
    ).fetchone()

    if row is None:
        return insights_pros, insights_cons

    columns = [desc[0] for desc in conn.execute(
        "SELECT * FROM financial_ratios LIMIT 1"
    ).description]
    data = dict(zip(columns, row))

    def get(col):
        return data.get(col)

    roe = get("return_on_equity_pct")
    de = get("debt_to_equity")
    npm = get("net_profit_margin_pct")
    pe = get("pe_ratio") or get("price_to_earnings")

    if roe is not None:
        if roe > 20:
            insights_pros.append(f"Strong return on equity of {roe:.1f}%.")
        elif roe < 5:
            insights_cons.append(f"Weak return on equity of {roe:.1f}%.")

    if de is not None:
        if de < 0.5:
            insights_pros.append(f"Low leverage with debt-to-equity of {de:.2f}x.")
        elif de > 2:
            insights_cons.append(f"High leverage with debt-to-equity of {de:.2f}x.")

    if npm is not None:
        if npm > 15:
            insights_pros.append(f"Healthy net profit margin of {npm:.1f}%.")
        elif npm < 3:
            insights_cons.append(f"Thin net profit margin of {npm:.1f}%.")

    if pe is not None:
        if pe > 40:
            insights_cons.append(f"Elevated valuation with P/E of {pe:.1f}x.")
        elif pe < 15 and pe > 0:
            insights_pros.append(f"Attractive valuation with P/E of {pe:.1f}x.")

    return insights_pros, insights_cons


def build_company_summary(conn, company_id):
    text_pros, text_cons = aggregate_pros_cons(conn, company_id)
    ratio_pros, ratio_cons = generate_ratio_insights(conn, company_id)

    all_pros = list(dict.fromkeys(text_pros + ratio_pros))
    all_cons = list(dict.fromkeys(text_cons + ratio_cons))
    if not all_pros and not all_cons:
        all_pros = ["No standout strengths or weaknesses on the tracked ratios."]

    return {
        "company_id": company_id,
        "pros": all_pros,
        "cons": all_cons
    }
def build_all_summaries(db_path="data/nifty100.db"):
    conn = get_connection(db_path)
    company_ids = [r[0] for r in conn.execute(
        "SELECT DISTINCT company_id FROM financial_ratios"
    ).fetchall()]

    summaries = []
    for cid in company_ids:
        summaries.append(build_company_summary(conn, cid))

    conn.close()
    return summaries


def save_summaries_to_db(summaries, db_path="data/nifty100.db"):
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nlp_insights (
            company_id TEXT PRIMARY KEY,
            pros_summary TEXT,
            cons_summary TEXT
        )
    """)
    for s in summaries:
        conn.execute(
            "INSERT OR REPLACE INTO nlp_insights (company_id, pros_summary, cons_summary) VALUES (?, ?, ?)",
            (s["company_id"], " | ".join(s["pros"]), " | ".join(s["cons"]))
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    summaries = build_all_summaries()
    print(f"Generated insights for {len(summaries)} companies.")
    print("Sample:", summaries[0] if summaries else "No data found.")
    save_summaries_to_db(summaries)
    print("Saved to nlp_insights table in database.")
