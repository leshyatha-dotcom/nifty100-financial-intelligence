import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "analytics"))

from ratios import (
    net_profit_margin, operating_profit_margin, opm_cross_check,
    return_on_equity, return_on_capital_employed, return_on_assets,
    debt_to_equity, high_leverage_flag, interest_coverage, icr_label,
    icr_warning_flag, net_debt, asset_turnover,
)


def test_npm_normal_case():
    assert net_profit_margin(100, 1000) == 10.0


def test_npm_zero_sales_returns_none():
    assert net_profit_margin(100, 0) is None


def test_opm_normal_case():
    assert operating_profit_margin(200, 1000) == 20.0


def test_opm_zero_sales_returns_none():
    assert operating_profit_margin(200, 0) is None


def test_roe_normal_case():
    assert return_on_equity(100, 400, 100) == 20.0


def test_roe_negative_equity_returns_none():
    assert return_on_equity(100, -100, -50) is None


def test_opm_cross_check_mismatch_flagged():
    assert opm_cross_check(computed_opm=15.0, source_opm_pct=12.0) is True


def test_opm_cross_check_within_tolerance_not_flagged():
    assert opm_cross_check(computed_opm=15.2, source_opm_pct=15.0) is False


def test_roce_normal_case():
    val = return_on_capital_employed(300, 50, 400, 100, 200)
    assert round(val, 2) == round(250 / 700 * 100, 2)


def test_roce_zero_capital_employed_returns_none():
    assert return_on_capital_employed(300, 50, 0, 0, 0) is None


def test_roa_normal_case():
    assert return_on_assets(100, 1000) == 10.0


def test_roa_zero_assets_returns_none():
    assert return_on_assets(100, 0) is None


def test_de_debt_free_returns_zero():
    assert debt_to_equity(0, 400, 100) == 0.0


def test_de_normal_case():
    assert debt_to_equity(200, 400, 100) == 0.4


def test_de_zero_equity_with_debt_returns_none():
    assert debt_to_equity(200, 0, 0) is None


def test_high_leverage_flag_true_for_non_financial():
    assert high_leverage_flag(6.0, "Industrials") is True


def test_high_leverage_flag_false_for_financials_sector():
    assert high_leverage_flag(6.0, "Financials") is False


def test_icr_interest_zero_returns_none():
    assert interest_coverage(300, 50, 0) is None


def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"


def test_icr_label_none_when_value_present():
    assert icr_label(5.0) is None


def test_icr_normal_case():
    assert interest_coverage(300, 50, 100) == 3.5


def test_icr_warning_flag_triggered():
    assert icr_warning_flag(1.2) is True


def test_icr_warning_flag_not_triggered():
    assert icr_warning_flag(2.0) is False


def test_net_debt_positive():
    assert net_debt(500, 100) == 400


def test_net_debt_negative_when_cash_rich():
    assert net_debt(100, 500) == -400


def test_asset_turnover_normal_case():
    assert asset_turnover(1000, 500) == 2.0


def test_asset_turnover_zero_assets_returns_none():
    assert asset_turnover(1000, 0) is None
