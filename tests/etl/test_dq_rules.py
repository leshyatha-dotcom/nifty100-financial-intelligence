import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "etl"))

import pandas as pd
from validator import run_all_checks


def _frames(companies=None, pl=None, bs=None, cf=None, sectors=None, documents=None):
    base = pd.DataFrame({"id": ["TCS"], "company_name": ["Tata Consultancy"]})
    return {
        "companies": companies if companies is not None else base,
        "profitandloss": pl if pl is not None else pd.DataFrame(
            columns=["company_id", "year", "sales", "net_profit", "operating_profit",
                     "opm_percentage", "tax_percentage", "dividend_payout", "eps"]),
        "balancesheet": bs if bs is not None else pd.DataFrame(
            columns=["company_id", "year", "total_assets", "total_liabilities", "fixed_assets"]),
        "cashflow": cf if cf is not None else pd.DataFrame(
            columns=["company_id", "year", "operating_activity", "investing_activity",
                     "financing_activity", "net_cash_flow"]),
        "sectors": sectors if sectors is not None else pd.DataFrame(columns=["company_id", "broad_sector"]),
        "documents": documents if documents is not None else pd.DataFrame(columns=["company_id", "Year", "Annual_Report"]),
    }


def _rule_ids(violations, rule_id):
    return [v for v in violations if v["rule_id"] == rule_id]


def test_dq01_duplicate_company_pk():
    companies = pd.DataFrame({"id": ["TCS", "TCS"], "company_name": ["A", "B"]})
    frames = _frames(companies=companies)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-01")
    assert len(hits) == 1
    assert hits[0]["severity"] == "CRITICAL"


def test_dq02_duplicate_annual_pk():
    pl = pd.DataFrame({
        "company_id": ["TCS", "TCS"], "year": ["2023-03", "2023-03"],
        "sales": [100, 100], "net_profit": [10, 10], "operating_profit": [20, 20],
        "opm_percentage": [20, 20], "tax_percentage": [25, 25], "dividend_payout": [30, 30],
        "eps": [5, 5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-02")
    assert len(hits) >= 1
    assert hits[0]["severity"] == "CRITICAL"


def test_dq03_fk_orphan():
    pl = pd.DataFrame({
        "company_id": ["UNKNOWN"], "year": ["2023-03"], "sales": [100], "net_profit": [10],
        "operating_profit": [20], "opm_percentage": [20], "tax_percentage": [25],
        "dividend_payout": [30], "eps": [5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-03")
    assert len(hits) == 1
    assert hits[0]["severity"] == "CRITICAL"


def test_dq04_balance_sheet_imbalance():
    bs = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "total_assets": [1000], "total_liabilities": [1020], "fixed_assets": [100],
    })
    frames = _frames(bs=bs)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-04")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq05_opm_cross_check_mismatch():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"], "sales": [1000], "net_profit": [100],
        "operating_profit": [150], "opm_percentage": [10.0],  # computed=15%, source=10% -> >1pt diff
        "tax_percentage": [25], "dividend_payout": [30], "eps": [5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-05")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq06_zero_sales():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"], "sales": [0], "net_profit": [10],
        "operating_profit": [20], "opm_percentage": [20], "tax_percentage": [25],
        "dividend_payout": [30], "eps": [5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-06")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq09_net_cash_mismatch():
    cf = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "operating_activity": [100], "investing_activity": [-50],
        "financing_activity": [-10], "net_cash_flow": [100],  # should be ~40, off by 60
    })
    frames = _frames(cf=cf)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-09")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq10_negative_fixed_assets():
    bs = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "total_assets": [1000], "total_liabilities": [1000], "fixed_assets": [-5],
    })
    frames = _frames(bs=bs)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-10")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq11_tax_rate_out_of_range():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"], "sales": [1000], "net_profit": [100],
        "operating_profit": [200], "opm_percentage": [20], "tax_percentage": [75],
        "dividend_payout": [30], "eps": [5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-11")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq12_dividend_payout_cap():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"], "sales": [1000], "net_profit": [100],
        "operating_profit": [200], "opm_percentage": [20], "tax_percentage": [25],
        "dividend_payout": [250], "eps": [5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-12")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq13_missing_annual_report_url():
    documents = pd.DataFrame({"company_id": ["TCS"], "Year": [2024], "Annual_Report": [None]})
    frames = _frames(documents=documents)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-13")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq14_eps_sign_mismatch():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"], "sales": [1000], "net_profit": [100],
        "operating_profit": [200], "opm_percentage": [20], "tax_percentage": [25],
        "dividend_payout": [30], "eps": [-5],  # net_profit > 0 but eps <= 0
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-14")
    assert len(hits) == 1
    assert hits[0]["severity"] == "WARNING"


def test_dq16_insufficient_year_coverage():
    pl = pd.DataFrame({
        "company_id": ["TCS", "TCS"], "year": ["2022-03", "2023-03"],
        "sales": [900, 1000], "net_profit": [90, 100], "operating_profit": [180, 200],
        "opm_percentage": [20, 20], "tax_percentage": [25, 25], "dividend_payout": [30, 30],
        "eps": [4, 5],
    })
    frames = _frames(pl=pl)
    violations = run_all_checks(frames)
    hits = _rule_ids(violations, "DQ-16")
    assert len(hits) >= 1
    assert hits[0]["severity"] == "WARNING"


def test_no_violations_on_clean_data():
    pl = pd.DataFrame({
        "company_id": ["TCS"] * 6, "year": [f"20{y}-03" for y in range(18, 24)],
        "sales": [1000, 1100, 1200, 1300, 1400, 1500],
        "net_profit": [100, 110, 120, 130, 140, 150],
        "operating_profit": [200, 220, 240, 260, 280, 300],
        "opm_percentage": [20, 20, 20, 20, 20, 20],
        "tax_percentage": [25] * 6, "dividend_payout": [30] * 6, "eps": [5, 5.5, 6, 6.5, 7, 7.5],
    })
    bs = pd.DataFrame({
        "company_id": ["TCS"] * 6, "year": [f"20{y}-03" for y in range(18, 24)],
        "total_assets": [1000] * 6, "total_liabilities": [1000] * 6, "fixed_assets": [100] * 6,
    })
    cf = pd.DataFrame({
        "company_id": ["TCS"] * 6, "year": [f"20{y}-03" for y in range(18, 24)],
        "operating_activity": [100] * 6, "investing_activity": [-50] * 6,
        "financing_activity": [-10] * 6, "net_cash_flow": [40] * 6,
    })
    frames = _frames(pl=pl, bs=bs, cf=cf)
    violations = run_all_checks(frames)
    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    assert len(critical) == 0
