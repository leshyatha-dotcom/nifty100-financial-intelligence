"""Shared, cached data-access layer for the Streamlit dashboard."""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "nifty100.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def load_table(table: str) -> pd.DataFrame:
    """Load an entire table from nifty100.db, cached for 10 minutes."""
    with _connect() as conn:
        return pd.read_sql(f"SELECT * FROM {table}", conn)


@st.cache_data(ttl=600)
def load_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run an arbitrary parameterised query, cached for 10 minutes."""
    with _connect() as conn:
        return pd.read_sql(sql, conn, params=params)


@st.cache_data(ttl=600)
def company_list() -> pd.DataFrame:
    return load_query(
        """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        ORDER BY c.company_name
        """
    )


@st.cache_data(ttl=600)
def latest_ratios() -> pd.DataFrame:
    """financial_ratios, one row per company: the most recent year available."""
    fr = load_table("financial_ratios")
    return fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)
