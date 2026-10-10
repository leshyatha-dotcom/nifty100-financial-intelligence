-- Sprint 1, Day 7 deliverable: exploratory_queries.sql
-- Run against data/nifty100.db

-- 1. Row counts per table
SELECT 'companies' AS tbl, COUNT(*) AS n FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 2. Null counts in profitandloss key fields
SELECT
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
FROM profitandloss;

-- 3. Year coverage (min/max/count of distinct years) per table
SELECT 'profitandloss' AS tbl, MIN(year) AS min_yr, MAX(year) AS max_yr, COUNT(DISTINCT year) AS n_years FROM profitandloss
UNION ALL SELECT 'balancesheet', MIN(year), MAX(year), COUNT(DISTINCT year) FROM balancesheet
UNION ALL SELECT 'cashflow', MIN(year), MAX(year), COUNT(DISTINCT year) FROM cashflow;

-- 4. Companies with fewer than 5 years of P&L history (DQ-16 coverage check)
SELECT company_id, COUNT(*) AS years_of_data
FROM profitandloss
GROUP BY company_id
HAVING COUNT(*) < 5
ORDER BY years_of_data;

-- 5. Sector distribution (company count per broad_sector)
SELECT broad_sector, COUNT(*) AS n_companies
FROM sectors
GROUP BY broad_sector
ORDER BY n_companies DESC;

-- 6. Debt-free companies in the latest year available in balancesheet
SELECT company_id, year, borrowings
FROM balancesheet
WHERE borrowings = 0
ORDER BY year DESC
LIMIT 20;

-- 7. Companies present in stock_prices but missing from financial_ratios (coverage gap)
SELECT DISTINCT sp.company_id
FROM stock_prices sp
LEFT JOIN financial_ratios fr ON sp.company_id = fr.company_id
WHERE fr.company_id IS NULL;

-- 8. Peer group membership counts
SELECT peer_group_name, COUNT(*) AS n_members
FROM peer_groups
GROUP BY peer_group_name
ORDER BY n_members DESC;

-- 9. Companies with missing annual report links (coverage gap in documents)
SELECT c.id, c.company_name, COUNT(d.id) AS n_reports
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
GROUP BY c.id
HAVING n_reports = 0;

-- 10. Top 10 companies by latest-year market cap
SELECT company_id, year, market_cap_crore
FROM market_cap
WHERE year = (SELECT MAX(year) FROM market_cap)
ORDER BY market_cap_crore DESC
LIMIT 10;
