"""
Cash flow KPIs and capital allocation pattern classifier.
Per project spec Sprint 2 Day 11 and Section 13 (KPI Reference).
"""


def free_cash_flow(operating_activity, investing_activity):
    """FCF = CFO + CFI. Negative values are allowed."""
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_score(cfo_values, pat_values):
    """CFO/PAT ratio averaged over the given years. Returns (score_or_None, label_or_None)."""
    if not cfo_values or not pat_values or len(cfo_values) != len(pat_values):
        return None, None
    ratios = []
    for cfo, pat in zip(cfo_values, pat_values):
        if pat == 0 or pat is None or cfo is None:
            continue
        ratios.append(cfo / pat)
    if not ratios:
        return None, None
    avg_ratio = sum(ratios) / len(ratios)
    if avg_ratio > 1.0:
        label = "High Quality Earnings"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return avg_ratio, label


def capex_intensity(investing_activity, sales):
    """CapEx / Revenue % = abs(investing_activity) / sales * 100."""
    if sales in (0, None):
        return None, None
    pct = abs(investing_activity or 0) / sales * 100
    if pct < 3:
        label = "Asset Light"
    elif pct <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return pct, label


def fcf_conversion_rate(fcf, operating_profit):
    """FCF / EBITDA(operating_profit) * 100. None if operating_profit == 0."""
    if operating_profit in (0, None):
        return None
    return (fcf / operating_profit) * 100


def capex_cr(investing_activity):
    """CapEx proxy in Crore = abs(investing_activity)."""
    return abs(investing_activity or 0)


_PATTERN_LABELS = {
    ("+", "-", "-"): "Reinvestor / Shareholder Returns",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
    ("-", "+", "-"): "Mixed",
}


def _sign(value):
    if value is None:
        return "0"
    if value > 0:
        return "+"
    if value < 0:
        return "-"
    return "0"


def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    """Classify a company-year into one of the 8 CFO/CFI/CFF sign patterns."""
    cfo_s, cfi_s, cff_s = _sign(cfo), _sign(cfi), _sign(cff)
    key = (cfo_s, cfi_s, cff_s)
    label = _PATTERN_LABELS.get(key, "Undefined")

    if key == ("+", "-", "-") and cfo_pat_ratio is not None:
        label = "Shareholder Returns" if cfo_pat_ratio > 1.5 else "Reinvestor"

    return cfo_s, cfi_s, cff_s, label
