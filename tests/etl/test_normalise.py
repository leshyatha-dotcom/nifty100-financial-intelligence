import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "etl"))

import pytest
from normaliser import normalize_year, normalize_ticker


# ---------------------------------------------------------------------------
# normalize_year - 20 cases (spec requirement: 20 cases)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("Mar-23", "2023-03"),
    ("Mar 23", "2023-03"),
    ("March-2023", "2023-03"),
    ("2023", "2023-03"),
    ("FY23", "2023-03"),
    ("Dec-22", "2022-12"),
    ("Jun-23", "2023-06"),
    ("2023-03", "2023-03"),
    ("garbage", "PARSE_ERROR"),
    ("Jan-20", "2020-01"),
    ("Feb-21", "2021-02"),
    ("Apr-19", "2019-04"),
    ("May-18", "2018-05"),
    ("Jul-24", "2024-07"),
    ("Aug-17", "2017-08"),
    ("Sep-16", "2016-09"),
    ("Oct-15", "2015-10"),
    ("Nov-14", "2014-11"),
    ("", "PARSE_ERROR"),
    (None, "PARSE_ERROR"),
])
def test_normalize_year(raw, expected):
    assert normalize_year(raw) == expected


def test_normalize_year_fy_full_year():
    assert normalize_year("FY2024") == "2024-03"


def test_normalize_year_already_normalised_passthrough():
    assert normalize_year("2019-06") == "2019-06"


def test_normalize_year_december_year_end_company():
    # e.g. NESTLEIND has a December fiscal year end
    assert normalize_year("Dec-2022") == "2022-12"


def test_normalize_year_june_year_end_company():
    # some banks report June fiscal year end
    assert normalize_year("Jun-2023") == "2023-06"


def test_normalize_year_ttm_is_unparseable():
    # TTM (trailing twelve months) is not a fiscal year label
    assert normalize_year("TTM") == "PARSE_ERROR"


def test_normalize_year_malformed_with_extra_token():
    assert normalize_year("Mar 2016 9m") == "PARSE_ERROR"


def test_normalize_year_whitespace_stripped():
    assert normalize_year("  Mar-23  ") == "2023-03"


# ---------------------------------------------------------------------------
# normalize_ticker - 15 cases (spec requirement: 15 cases)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("TCS", "TCS"),
    ("tcs", "TCS"),
    (" TCS ", "TCS"),
    ("  tcs", "TCS"),
    ("BAJAJ-AUTO", "BAJAJ-AUTO"),
    ("bajaj-auto", "BAJAJ-AUTO"),
    ("M&M", "M&M"),
    ("m&m", "M&M"),
    ("HDFCBANK", "HDFCBANK"),
    ("Reliance", "RELIANCE"),
    ("infy", "INFY"),
    ("ITC", "ITC"),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_normalize_ticker(raw, expected):
    assert normalize_ticker(raw) == expected


def test_normalize_ticker_mixed_case_with_internal_hyphen():
    assert normalize_ticker("Tata-Steel") == "TATA-STEEL"


def test_normalize_ticker_numeric_input_coerced_to_string():
    assert normalize_ticker(123) == "123"
