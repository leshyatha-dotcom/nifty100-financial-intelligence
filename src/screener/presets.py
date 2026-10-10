"""
Sprint 3, Day 16: implement the 6 preset screeners from screener_config.yaml
and verify each returns a business-sensible result count on the full universe.

Two presets (Dividend Champion's max_dividend_payout, Turnaround Watch's
min_rev_cagr_3yr) reference filters not in the base `filters:` block or
columns not yet computed (3yr CAGR, dividend_payout in market_cap namespace) -
those are handled with small preset-specific logic here rather than forcing
everything through the generic engine.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import run_screener, build_universe, load_config, apply_filters
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"


def preset_quality_compounder(universe, config):
    filters = config["presets"]["quality_compounder"]["filters"]
    return apply_filters(universe, filters, config)


def preset_value_pick(universe, config):
    filters = config["presets"]["value_pick"]["filters"]
    return apply_filters(universe, filters, config)


def preset_growth_accelerator(universe, config):
    filters = config["presets"]["growth_accelerator"]["filters"]
    return apply_filters(universe, filters, config)


def preset_dividend_champion(universe, config):
    filters = {"min_dividend_yield": config["presets"]["dividend_champion"]["filters"]["min_dividend_yield"],
               "min_fcf": config["presets"]["dividend_champion"]["filters"]["min_fcf"]}
    result = apply_filters(universe, filters, config)
    max_payout = config["presets"]["dividend_champion"]["filters"]["max_dividend_payout"]
    result = result[result["dividend_payout_ratio_pct"] <= max_payout]
    return result


def preset_debt_free_blue_chip(universe, config):
    filters = config["presets"]["debt_free_blue_chip"]["filters"]
    return apply_filters(universe, filters, config)


def preset_turnaround_watch(universe, config):
    # Revenue CAGR 3yr isn't in financial_ratios (only 5yr is computed) - use 5yr as the
    # closest available proxy here and flag this as a follow-up to add a real 3yr column.
    filters = {"min_fcf": config["presets"]["turnaround_watch"]["filters"]["min_fcf"]}
    result = apply_filters(universe, filters, config)
    min_cagr = config["presets"]["turnaround_watch"]["filters"]["min_rev_cagr_3yr"]
    result = result[result["revenue_cagr_5yr"] >= min_cagr]
    return result


PRESET_FUNCS = {
    "Quality Compounder": preset_quality_compounder,
    "Value Pick": preset_value_pick,
    "Growth Accelerator": preset_growth_accelerator,
    "Dividend Champion": preset_dividend_champion,
    "Debt-Free Blue Chip": preset_debt_free_blue_chip,
    "Turnaround Watch": preset_turnaround_watch,
}

EXPECTED_RANGES = {
    "Quality Compounder": (15, 35),
    "Value Pick": (10, 25),
    "Growth Accelerator": (8, 20),
    "Dividend Champion": (10, 20),
    "Debt-Free Blue Chip": (15, 30),
    "Turnaround Watch": (5, 15),
}


def run_all_presets():
    conn = sqlite3.connect(DB_PATH)
    config = load_config()
    universe = build_universe(conn)
    conn.close()

    results = {}
    for name, func in PRESET_FUNCS.items():
        r = func(universe, config)
        results[name] = r.sort_values("composite_quality_score", ascending=False)
    return results


if __name__ == "__main__":
    results = run_all_presets()
    print(f"{'Preset':<22} {'Count':>6} {'Expected range':>16} {'In range?':>10}")
    print("-" * 60)
    for name, df in results.items():
        lo, hi = EXPECTED_RANGES[name]
        n = len(df)
        ok = "YES" if lo <= n <= hi else "NO - review"
        print(f"{name:<22} {n:>6} {f'[{lo}, {hi}]':>16} {ok:>10}")
