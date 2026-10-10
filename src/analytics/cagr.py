"""
CAGR (Compound Annual Growth Rate) engine.

Formula: ((end / start) ** (1/n) - 1) * 100

Edge cases per project spec Section 23.1 (CAGR Edge Case Decision Table):
    base > 0, end > 0   -> computed normally
    base > 0, end < 0   -> None, flag DECLINE_TO_LOSS
    base < 0, end > 0   -> None, flag TURNAROUND
    base < 0, end < 0   -> None, flag BOTH_NEGATIVE
    base == 0           -> None, flag ZERO_BASE
    < n years of history -> None, flag INSUFFICIENT
"""


def cagr(start_value, end_value, n_years, min_years_available=None):
    """Compute CAGR with all 6 edge-case flags.

    Returns (value_or_None, flag_or_None). flag is None only on a normal, computed result.
    """
    if min_years_available is not None and min_years_available < n_years:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value > 0:
        value = ((end_value / start_value) ** (1 / n_years) - 1) * 100
        return value, None

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    return None, "ZERO_BASE"
