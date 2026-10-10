import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "analytics"))

from cagr import cagr


def test_cagr_normal_growth():
    value, flag = cagr(100, 161, 5)
    assert flag is None
    assert round(value, 1) == 10.0


def test_cagr_turnaround_negative_to_positive():
    value, flag = cagr(-100, 200, 3)
    assert value is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss_positive_to_negative():
    value, flag = cagr(100, -50, 3)
    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_both_negative():
    value, flag = cagr(-100, -50, 3)
    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    value, flag = cagr(0, 100, 5)
    assert value is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_history():
    value, flag = cagr(100, 200, 5, min_years_available=2)
    assert value is None
    assert flag == "INSUFFICIENT"


def test_cagr_positive_growth_ten_year():
    value, flag = cagr(1000, 2593.7, 10)
    assert flag is None
    assert round(value, 1) == 10.0


def test_cagr_flat_growth_returns_zero_percent():
    value, flag = cagr(500, 500, 5)
    assert flag is None
    assert round(value, 4) == 0.0


def test_cagr_decline_but_still_positive():
    value, flag = cagr(1000, 800, 3)
    assert flag is None
    assert value < 0


def test_cagr_min_years_available_exactly_enough_computes_normally():
    value, flag = cagr(100, 200, 5, min_years_available=5)
    assert flag is None
    assert value is not None
