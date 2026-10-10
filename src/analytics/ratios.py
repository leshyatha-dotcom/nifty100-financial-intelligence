"""
Financial ratio engine: profitability, leverage, and efficiency ratios.
Formulas and edge cases per project spec Section 13 (KPI Reference) and
Sprint 2 Day 08-09 task list.
"""


def net_profit_margin(net_profit, sales):
    """NPM = net_profit / sales * 100. None if sales == 0."""
    if sales in (0, None) or sales == 0:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    """OPM = operating_profit / sales * 100. None if sales == 0."""
    if sales in (0, None) or sales == 0:
        return None
    return (operating_profit / sales) * 100


def opm_cross_check(computed_opm, source_opm_pct, tolerance=1.0):
    """Returns True if computed OPM differs from source opm_percentage by >= tolerance pts."""
    if computed_opm is None or source_opm_pct is None:
        return False
    return abs(computed_opm - source_opm_pct) >= tolerance


def return_on_equity(net_profit, equity_capital, reserves):
    """ROE = net_profit / (equity + reserves) * 100. None if equity+reserves <= 0."""
    equity_total = (equity_capital or 0) + (reserves or 0)
    if equity_total <= 0:
        return None
    return (net_profit / equity_total) * 100


def ebit(operating_profit, depreciation):
    """EBIT = operating_profit - depreciation."""
    return operating_profit - (depreciation or 0)


def return_on_capital_employed(operating_profit, depreciation, equity_capital, reserves, borrowings):
    """ROCE = EBIT / (equity + reserves + borrowings) * 100. None if capital employed <= 0."""
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return None
    return (ebit(operating_profit, depreciation) / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    """ROA = net_profit / total_assets * 100. None if total_assets == 0."""
    if total_assets in (0, None):
        return None
    return (net_profit / total_assets) * 100


def debt_to_equity(borrowings, equity_capital, reserves):
    """D/E = borrowings / (equity + reserves). Returns 0 (not None) for debt-free companies."""
    equity_total = (equity_capital or 0) + (reserves or 0)
    borrowings = borrowings or 0
    if borrowings == 0:
        return 0.0
    if equity_total <= 0:
        return None
    return borrowings / equity_total


def high_leverage_flag(de_ratio, broad_sector, threshold=5.0):
    """True if D/E > threshold AND company is NOT in the Financials sector."""
    if de_ratio is None or broad_sector == "Financials":
        return False
    return de_ratio > threshold


def interest_coverage(operating_profit, other_income, interest):
    """ICR = (operating_profit + other_income) / interest. None if interest == 0 (debt-free)."""
    if interest in (0, None):
        return None
    return (operating_profit + (other_income or 0)) / interest


def icr_label(icr_value):
    """Display label for ICR: 'Debt Free' when the ratio is None (interest == 0)."""
    return "Debt Free" if icr_value is None else None


def icr_warning_flag(icr_value, threshold=1.5):
    """True if ICR < threshold - company at risk of not covering interest payments."""
    if icr_value is None:
        return False
    return icr_value < threshold


def net_debt(borrowings, investments):
    """Net debt = borrowings - investments (investments used as liquid asset proxy)."""
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales, total_assets):
    """Asset turnover = sales / total_assets. None if total_assets == 0."""
    if total_assets in (0, None):
        return None
    return sales / total_assets
