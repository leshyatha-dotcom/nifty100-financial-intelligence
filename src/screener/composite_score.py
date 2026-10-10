"""
Sprint 3, Day 17: Composite Quality Score (0-100) per project spec Section 25.1.

Weights:
    Profitability 35%: ROE 15% + ROCE 10% + NPM 10%
    Cash Quality  30%: FCF CAGR 15% + CFO/PAT ratio 10% + FCF-positive flag 5%
    Growth        20%: Revenue CAGR 5yr 10% + PAT CAGR 5yr 10%
    Leverage      15%: D/E score 10% + ICR score 5%

Each raw metric is winsorised at P10/P90 then scaled to 0-100 before weighting.
A sector-relative variant computes the same score using each broad_sector's own
P10/P90 bounds, so companies are scored against sector peers rather than the
full Nifty 100 universe.
"""

import pandas as pd


def _winsorised_score(series, p10, p90, invert=False):
    if pd.isna(p10) or pd.isna(p90) or p90 == p10:
        return pd.Series([50.0] * len(series), index=series.index)
    clipped = series.clip(lower=p10, upper=p90)
    score = (clipped - p10) / (p90 - p10) * 100
    return 100 - score if invert else score


def _de_score(de_series):
    """D/E score per spec lookup table: 0=100, 0.5=85, 1=70, 2=50, >5=0 (piecewise linear)."""
    def score_one(de):
        if pd.isna(de):
            return 50.0
        points = [(0, 100), (0.5, 85), (1, 70), (2, 50), (5, 0)]
        if de >= 5:
            return 0.0
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 <= de <= x1:
                return y0 + (y1 - y0) * (de - x0) / (x1 - x0)
        return 0.0
    return de_series.apply(score_one)


def _icr_score(icr_series, icr_label_series):
    """ICR score: >10=100, 5=75, 3=50, <1.5=0 (piecewise linear). Debt Free -> 100."""
    def score_one(icr, label):
        if label == "Debt Free":
            return 100.0
        if pd.isna(icr):
            return 50.0
        points = [(1.5, 0), (3, 50), (5, 75), (10, 100)]
        if icr <= 1.5:
            return 0.0
        if icr >= 10:
            return 100.0
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 <= icr <= x1:
                return y0 + (y1 - y0) * (icr - x0) / (x1 - x0)
        return 100.0
    return pd.Series(
        [score_one(icr, lbl) for icr, lbl in zip(icr_series, icr_label_series)],
        index=icr_series.index,
    )


def compute_composite_score(df, group_col=None):
    """df must have: return_on_equity_pct, roce_pct, net_profit_margin_pct,
    revenue_cagr_5yr, pat_cagr_5yr, cfo_quality_score, free_cash_flow_cr,
    debt_to_equity, interest_coverage, icr_label.

    group_col: if provided (e.g. 'broad_sector'), computes sector-relative winsorisation
    bounds instead of universe-wide bounds.
    """
    result = df.copy()

    def score_group(g):
        roe_score = _winsorised_score(g["return_on_equity_pct"], g["return_on_equity_pct"].quantile(0.10), g["return_on_equity_pct"].quantile(0.90))
        roce_score = _winsorised_score(g["roce_pct"], g["roce_pct"].quantile(0.10), g["roce_pct"].quantile(0.90))
        npm_score = _winsorised_score(g["net_profit_margin_pct"], g["net_profit_margin_pct"].quantile(0.10), g["net_profit_margin_pct"].quantile(0.90))
        profitability = 0.15 * roe_score.fillna(0) + 0.10 * roce_score.fillna(0) + 0.10 * npm_score.fillna(0)

        rev_cagr_score = _winsorised_score(g["revenue_cagr_5yr"], g["revenue_cagr_5yr"].quantile(0.10), g["revenue_cagr_5yr"].quantile(0.90))
        cfo_pat_score = _winsorised_score(g["cfo_quality_score"], g["cfo_quality_score"].quantile(0.10), g["cfo_quality_score"].quantile(0.90))
        fcf_positive_flag = (g["free_cash_flow_cr"] > 0).astype(float) * 100
        cash_quality = 0.15 * rev_cagr_score.fillna(0) + 0.10 * cfo_pat_score.fillna(0) + 0.05 * fcf_positive_flag

        pat_cagr_score = _winsorised_score(g["pat_cagr_5yr"], g["pat_cagr_5yr"].quantile(0.10), g["pat_cagr_5yr"].quantile(0.90))
        growth = 0.10 * rev_cagr_score.fillna(0) + 0.10 * pat_cagr_score.fillna(0)

        de_score = _de_score(g["debt_to_equity"])
        icr_score = _icr_score(g["interest_coverage"], g["icr_label"])
        leverage = 0.10 * de_score.fillna(50) + 0.05 * icr_score.fillna(50)

        return (profitability + cash_quality + growth + leverage).round(1)

    if group_col and group_col in result.columns:
        result["composite_quality_score"] = result.groupby(group_col, group_keys=False).apply(score_group)
    else:
        result["composite_quality_score"] = score_group(result)

    return result
