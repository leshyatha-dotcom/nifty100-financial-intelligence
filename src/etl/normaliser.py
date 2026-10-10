"""
Normalisation utilities for the Nifty 100 Financial Intelligence Platform ETL pipeline.

- normalize_ticker(): strips/upper-cases NSE tickers so company_id joins cleanly across all 12 files.
- normalize_year(): standardises the many raw year formats found in the source files (e.g. "Mar-23",
  "FY24", "2023", "Dec-22") into a uniform 'YYYY-MM' string, per the ETL Edge Cases reference table
  in the project spec (Section 23).
"""

import re

# ---------------------------------------------------------------------------
# Ticker normalisation
# ---------------------------------------------------------------------------

def normalize_ticker(raw):
    """Strip whitespace and upper-case an NSE ticker / company_id.

    Returns None if the input is missing/blank (caller should reject the row - DQ-08).
    """
    if raw is None:
        return None
    ticker = str(raw).strip().upper()
    if not ticker:
        return None
    return ticker


# ---------------------------------------------------------------------------
# Year normalisation
# ---------------------------------------------------------------------------

_MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "sept": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

_ALREADY_NORMALISED = re.compile(r"^\d{4}-\d{2}$")
_MONTH_YEAR = re.compile(r"^([A-Za-z]+)[\s\-]+'?(\d{2,4})$")
_FY_PREFIX = re.compile(r"^FY\s*'?(\d{2,4})$", re.IGNORECASE)
_BARE_YEAR = re.compile(r"^\d{4}$")


def _expand_2digit_year(yy):
    """'23' -> 2023, '99' -> 1999 (never needed here but kept safe)."""
    yy = int(yy)
    return 2000 + yy if yy < 50 else 1900 + yy


def normalize_year(raw):
    """Standardise a raw year label to 'YYYY-MM'.

    Handles: 'Mar-23', 'Mar 23', 'March-2023', '2023' (bare -> assume March FY close,
    per spec), 'FY23', 'Dec-22', 'Jun-23', already-normalised 'YYYY-MM'.
    Returns 'PARSE_ERROR' for unparseable input (DQ-07: reject row, log raw value).
    """
    if raw is None:
        return "PARSE_ERROR"

    s = str(raw).strip()
    if not s:
        return "PARSE_ERROR"

    # Already normalised
    if _ALREADY_NORMALISED.match(s):
        return s

    # Bare 4-digit year -> assume March FY close
    if _BARE_YEAR.match(s):
        return f"{s}-03"

    # FY23 / FY 2023 style
    m = _FY_PREFIX.match(s)
    if m:
        yy = m.group(1)
        year = _expand_2digit_year(yy) if len(yy) == 2 else int(yy)
        return f"{year}-03"

    # "Mar-23", "Mar 23", "March-2023", "Dec-22", "Jun-23"
    m = _MONTH_YEAR.match(s)
    if m:
        month_raw, yy = m.group(1).lower(), m.group(2)
        month = _MONTH_MAP.get(month_raw)
        if month is None:
            return "PARSE_ERROR"
        year = _expand_2digit_year(yy) if len(yy) == 2 else int(yy)
        return f"{year}-{month}"

    return "PARSE_ERROR"


if __name__ == "__main__":
    # quick smoke test
    cases = [
        ("Mar-23", "2023-03"),
        ("Mar 23", "2023-03"),
        ("March-2023", "2023-03"),
        ("2023", "2023-03"),
        ("FY23", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("2023-03", "2023-03"),
        ("garbage", "PARSE_ERROR"),
    ]
    for raw, expected in cases:
        got = normalize_year(raw)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: normalize_year({raw!r}) = {got!r} (expected {expected!r})")

    tick_cases = [(" tcs ", "TCS"), ("BAJAJ-AUTO", "BAJAJ-AUTO"), ("m&m", "M&M")]
    for raw, expected in tick_cases:
        got = normalize_ticker(raw)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: normalize_ticker({raw!r}) = {got!r} (expected {expected!r})")
