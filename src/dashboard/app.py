"""Nifty 100 Financial Intelligence Platform - Streamlit dashboard entry point.

Run with: streamlit run src/dashboard/app.py
"""
import sys
from pathlib import Path

import streamlit as st

# Make sibling packages (utils) importable when run via `streamlit run`
sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="Nifty 100 Financial Intelligence Platform",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("\U0001F4CA Nifty 100 Platform")
st.sidebar.caption("Financial Intelligence · 92 Companies")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Use the **Home**, **Company Profile**, **Screener**, **Peer Comparison**, "
    "**Trend Analysis**, **Sector Analysis**, **Capital Allocation**, and "
    "**Annual Reports** pages in the left navigation."
)
st.sidebar.markdown("---")
st.sidebar.caption("Simulated datasets: stock prices & market cap are simulated for demo purposes.")

st.title("Nifty 100 Financial Intelligence Platform")
st.markdown(
    "Welcome. Select a page from the sidebar to explore company fundamentals, "
    "run the screener, compare peers, or review sector trends."
)
st.info("\u2190 Start with **Home** in the sidebar for the portfolio overview.")
