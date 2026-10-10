# Nifty 100 Financial Intelligence Platform

## Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Sprint 1 - Data Foundation
```
python3 src/etl/run_etl.py
```

## Sprint 2 - Financial Ratio Engine
```
python3 src/analytics/build_financial_ratios.py
```

## Sprint 3 - Screener & Peer Comparison
```
python3 src/screener/export_screener_output.py   # screener_output.xlsx (6 sheets)
python3 src/analytics/peer.py                     # peer_percentiles table
python3 src/screener/radar_charts.py              # 90 radar PNGs
python3 src/analytics/export_peer_comparison.py   # peer_comparison.xlsx (11 sheets)
```

## Sprint 4 - Dashboard & Valuation
```
python3 src/analytics/valuation.py                # valuation_summary.xlsx + valuation_flags.csv
streamlit run src/dashboard/app.py                # Streamlit app on http://localhost:8501
```
8 screens: Home, Company Profile, Screener, Peer Comparison, Trend Analysis, Sector Analysis,
Capital Allocation Map, Annual Reports. See `reports/dashboard_qa.md` for the QA log.

## Sprint 5 - NLP and Radar Charts
```
python src/nlp/pros_cons_generator.py
python src/screener/radar_charts.py
```
## Sprint 6 - API
```
uvicorn src.api.main:app --reload
```

## Tests
```
pytest tests/ -v
```
95 tests passing (ETL 44 + KPI formulas 37 + DQ rules 14).

## Dependencies added in Sprint 4
`streamlit`, `plotly` (added to requirements.txt).

## Known issues / data findings (flag to team lead)
- `financial_ratios` has 1,041 rows vs spec target of >=1,100 - cashflow.xlsx has fewer
  source rows than profitandloss.xlsx/balancesheet.xlsx, capping the 3-way join.
- BEL, HAL show implausible ROE (>3000%) for FY24 - traced to suspiciously low `reserves`
  values in balancesheet.xlsx. INDIGO shows 892% ROE for the same reason. Composite score
  winsorisation (P10/P90) correctly contains the distortion, but the underlying source data
  should be checked.
- SBIN has ZERO rows in balancesheet.xlsx - completely missing balance sheet data for
  India's largest bank. ATGL has zero rows in cashflow.xlsx. Both are excluded from
  financial_ratios, the screener, and radar charts as a result (90 of 92 companies covered).
- 36 orphan-ticker rows (WIPRO, ZOMATO, VEDL, etc.) reference companies not present in
  companies.xlsx's 92-row master - rejected per DQ-03, logged in validation_failures.csv.
- Value Pick screener preset thresholds were recalibrated (max_pe 20->36, max_pb 3.0->6.5)
  because the simulated market_cap.xlsx has a much richer valuation distribution
  (median P/E ~46x, median P/B ~7.7x) than the spec's original thresholds assumed.
## Clustering
```
python src/analytics/clustering.py
python src/reports/tearsheet_generator.py
```
ROE and ROCE are capped at 100 for clustering, because some companies (INDIGO, BEL, HAL, ICICIPRULI, HDFCLIFE) have near-zero equity in the source data.