# Sprint 4 Dashboard QA Log

## Smoke test
- `streamlit run src/dashboard/app.py` boots cleanly (HTTP 200 on localhost:8501).
- All 9 dashboard files (app.py + 8 pages + utils) pass `py_compile`.

## Screens verified against nifty100.db
1. Home / Overview - sector filter, KPI tiles, sector donut + median-ROE bar chart.
2. Company Profile - ticker search, KPI tiles, P&L/BS/CF tabs and charts.
3. Financial Screener - 4 presets (Custom/Quality Compounder/Value Pick/Debt-Free Blue Chip),
   sidebar sliders, CSV download.
4. Peer Comparison - group + company selectors, radar chart vs peer group average,
   percentile-rank table (10 metrics x 11 groups confirmed present in peer_percentiles).
5. Trend Analysis - multi-metric overlay (up to 3), YoY change annotation, CSV download.
6. Sector Analysis - bubble chart (revenue vs ROE, size=mkt cap), sector median KPI bar chart.
7. Capital Allocation Map - year slider, pattern bar chart, drill-down to company list.
8. Annual Reports - ticker + year filter, graceful "Report unavailable" for missing/blank URLs.

## Known data-driven edge cases (carried from Sprint 1-3 findings, still relevant here)
- SBIN (no balance sheet rows) and ATGL (no cash flow rows) will show "No ratio history
  available" on Company Profile / Trend Analysis pages - expected, not a bug.
- BEL, HAL, INDIGO show extreme ROE in raw financial_ratios; the Screener's composite score
  is winsorised so this doesn't distort ranking, but their raw ROE tile on Company Profile
  will show the anomalous value as-is (by design - it's the source data, not the score).
- 2 of 92 companies are missing from reports/radar_charts (90 PNGs present) for the same
  data-completeness reasons documented in README.md.

## Not yet built (belongs to Sprint 4 Module 6 exit criteria, done separately)
- valuation_summary.xlsx / valuation_flags.csv: built via `python src/analytics/valuation.py`
  (92 companies, 44 flagged: 14 Caution / 30 Discount vs sector median P/E). Not yet wired
  into a dedicated dashboard screen - spec allows this ("integrate valuation screen if time
  permits"); can add a 9th page in a follow-up if wanted.
