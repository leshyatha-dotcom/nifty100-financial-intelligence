"""
Full Sprint-1 ETL run: loads all 12 source files, normalises, deduplicates,
validates (16 DQ rules), writes to SQLite (10 tables), and emits:
  - db/nifty100.db
  - output/load_audit.csv
  - output/validation_failures.csv
"""

from pathlib import Path
import sqlite3
import time

import pandas as pd

from loader import load_all, ALL_FILES
from validator import run_all_checks

BASE_DIR = Path(__file__).resolve().parents[2]

# Map source table name -> SQLite table name / column rename needed
TABLE_MAP = {
    "companies": "companies",
    "profitandloss": "profitandloss",
    "balancesheet": "balancesheet",
    "cashflow": "cashflow",
    "analysis": "analysis",
    "documents": "documents",
    "prosandcons": "prosandcons",
    "sectors": "sectors",
    "stock_prices": "stock_prices",
    "market_cap": "market_cap",
    "financial_ratios": "financial_ratios",
    "peer_groups": "peer_groups",
}

# (company_id, year) dedupe key per table; None = no dedupe applied
DEDUPE_KEYS = {
    "profitandloss": ["company_id", "year"],
    "balancesheet": ["company_id", "year"],
    "cashflow": ["company_id", "year"],
    "financial_ratios": ["company_id", "year"],
    "market_cap": ["company_id", "year"],
    "stock_prices": ["company_id", "date"],
}


def dedupe(name, df, audit_row):
    key = DEDUPE_KEYS.get(name)
    if not key or not set(key).issubset(df.columns):
        return df
    before = len(df)
    # Keep last occurrence, per spec Day05/DQ-02
    df = df.drop_duplicates(subset=key, keep="last")
    removed = before - len(df)
    audit_row["duplicates_removed"] = removed
    return df


def enforce_fk(frames):
    """DQ-03: drop rows whose company_id doesn't exist in companies, for every child table."""
    valid_ids = set(frames["companies"]["id"].dropna())
    orphans_removed = {}
    for name, df in frames.items():
        if name == "companies" or "company_id" not in df.columns:
            continue
        before = len(df)
        frames[name] = df[df["company_id"].isin(valid_ids)]
        orphans_removed[name] = before - len(frames[name])
    return frames, orphans_removed


def main():
    t0 = time.time()
    frames, audit_rows = load_all(base_dir=BASE_DIR)
    audit_by_table = {a["table"]: a for a in audit_rows}

    # Dedupe time-series tables (Day 5 dedup engine, DQ-02)
    for name, df in frames.items():
        frames[name] = dedupe(name, df, audit_by_table[name])

    # Enforce FK integrity (DQ-03) - reject orphan rows before loading into SQLite
    frames, orphans_removed = enforce_fk(frames)
    for name, n in orphans_removed.items():
        audit_by_table[name]["orphans_removed"] = n
        audit_by_table[name]["rows_out"] = len(frames[name])

    # Run full DQ validation on the (deduped, FK-clean) data for reporting
    violations = run_all_checks(frames)
    critical = [v for v in violations if v["severity"] == "CRITICAL"]

    # Write to SQLite per db/schema.sql
    db_path = BASE_DIR / "data" / "nifty100.db"
    schema_path = BASE_DIR / "db" / "schema.sql"
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(schema_path.read_text())
    conn.execute("PRAGMA foreign_keys = ON")

    col_rename = {"annual_report": "Annual_Report"}  # documents table special-cases capital column names

    for name, df in frames.items():
        sql_name = TABLE_MAP[name]
        df_to_write = df.copy()
        if name == "documents":
            df_to_write = df_to_write.rename(columns={"Annual_Report": "annual_report", "Year": "year"})
        df_to_write.to_sql(sql_name, conn, if_exists="append", index=False)

    conn.commit()

    # FK check
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    runtime = time.time() - t0

    # Write load_audit.csv
    audit_out = BASE_DIR / "output" / "load_audit.csv"
    audit_out.parent.mkdir(exist_ok=True)
    audit_df = pd.DataFrame(audit_rows)
    audit_df["runtime_s"] = round(runtime, 2)
    audit_df.to_csv(audit_out, index=False)

    # Write validation_failures.csv
    val_out = BASE_DIR / "output" / "validation_failures.csv"
    pd.DataFrame(violations).to_csv(val_out, index=False)

    print(f"ETL complete in {runtime:.2f}s")
    print(f"  companies rows: {len(frames['companies'])}")
    print(f"  DB written to: {db_path}")
    print(f"  FK check violations: {len(fk_violations)}")
    print(f"  DQ violations: {len(violations)} (CRITICAL={len(critical)})")
    print(f"  load_audit.csv -> {audit_out}")
    print(f"  validation_failures.csv -> {val_out}")

    return {
        "companies_count": len(frames["companies"]),
        "fk_violations": len(fk_violations),
        "critical_dq": len(critical),
    }


if __name__ == "__main__":
    main()
