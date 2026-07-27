-- N100 Financial Intelligence Platform -- Sprint 1 exploratory queries
-- Run against nifty100.db. Monetary amounts are reported in the source unit
-- (crore INR for the current surrogate dataset).

-- 1. Top 10 companies by sales in the latest available reporting year.
WITH latest_year AS (
    SELECT MAX(year) AS year FROM profitandloss
)
SELECT p.company_id, c.company_name, c.sector, p.year, p.sales
FROM profitandloss AS p
JOIN companies AS c ON c.company_id = p.company_id
JOIN latest_year AS ly ON ly.year = p.year
ORDER BY p.sales DESC NULLS LAST
LIMIT 10;

-- 2. Top 10 companies by net profit in the latest available reporting year.
WITH latest_year AS (
    SELECT MAX(year) AS year FROM profitandloss
)
SELECT p.company_id, c.company_name, c.sector, p.year, p.net_profit
FROM profitandloss AS p
JOIN companies AS c ON c.company_id = p.company_id
JOIN latest_year AS ly ON ly.year = p.year
ORDER BY p.net_profit DESC NULLS LAST
LIMIT 10;

-- 3. Most leveraged companies: latest balance-sheet borrowings and source debt.
WITH latest_balance_sheet AS (
    SELECT company_id, MAX(year) AS year
    FROM balancesheet
    GROUP BY company_id
)
SELECT c.company_id, c.company_name, c.sector, b.year,
       b.borrowings AS total_borrowings_cr, c.debt_cr AS source_total_debt_cr,
       CASE
           WHEN b.equity_capital + b.reserves > 0
           THEN ROUND(b.borrowings / (b.equity_capital + b.reserves), 4)
       END AS debt_to_equity
FROM companies AS c
JOIN latest_balance_sheet AS lb ON lb.company_id = c.company_id
JOIN balancesheet AS b ON b.company_id = lb.company_id AND b.year = lb.year
ORDER BY debt_to_equity DESC NULLS LAST, b.borrowings DESC NULLS LAST
LIMIT 10;

-- 4. Twelve-year sales trend for the latest-year top 10 companies.
WITH latest_year AS (
    SELECT MAX(year) AS year FROM profitandloss
),
top_companies AS (
    SELECT company_id
    FROM profitandloss
    WHERE year = (SELECT year FROM latest_year)
    ORDER BY sales DESC NULLS LAST
    LIMIT 10
)
SELECT p.company_id, c.company_name, p.year, p.sales,
       ROUND(
           100.0 * (p.sales - LAG(p.sales) OVER company_years)
           / NULLIF(LAG(p.sales) OVER company_years, 0),
           2
       ) AS year_over_year_sales_growth_pct
FROM profitandloss AS p
JOIN top_companies AS tc ON tc.company_id = p.company_id
JOIN companies AS c ON c.company_id = p.company_id
WINDOW company_years AS (PARTITION BY p.company_id ORDER BY p.year)
ORDER BY p.company_id, p.year;

-- 5. Sector composition and total company market capitalisation.
SELECT COALESCE(sector, 'Unclassified') AS sector,
       COUNT(*) AS company_count,
       ROUND(SUM(market_cap_cr), 2) AS total_market_cap_cr,
       ROUND(AVG(market_cap_cr), 2) AS average_market_cap_cr
FROM companies
GROUP BY COALESCE(sector, 'Unclassified')
ORDER BY total_market_cap_cr DESC NULLS LAST, company_count DESC;

-- 6. OPM performance in the latest year, including change from the prior year.
WITH ranked_opm AS (
    SELECT p.company_id, p.year, p.opm_pct,
           LAG(p.opm_pct) OVER (PARTITION BY p.company_id ORDER BY p.year) AS prior_opm_pct,
           ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.year DESC) AS year_rank
    FROM profitandloss AS p
)
SELECT r.company_id, c.company_name, c.sector, r.year, r.opm_pct,
       r.prior_opm_pct,
       ROUND(r.opm_pct - r.prior_opm_pct, 2) AS opm_change_percentage_points
FROM ranked_opm AS r
JOIN companies AS c ON c.company_id = r.company_id
WHERE r.year_rank = 1
ORDER BY r.opm_pct DESC NULLS LAST;

-- 7. Cash-flow quality trend: operating cash flow versus net profit by year.
SELECT c.company_id, c.company_name, cf.year,
       cf.cash_from_operating_activity AS operating_cash_flow,
       p.net_profit,
       ROUND(
           cf.cash_from_operating_activity / NULLIF(p.net_profit, 0), 2
       ) AS operating_cash_flow_to_net_profit
FROM cashflow AS cf
JOIN profitandloss AS p
    ON p.company_id = cf.company_id AND p.year = cf.year
JOIN companies AS c ON c.company_id = cf.company_id
ORDER BY c.company_name, cf.year;

-- 8. Companies profitable in every one of the 12 loaded years.
SELECT p.company_id, c.company_name, c.sector,
       COUNT(DISTINCT p.year) AS profitable_year_count,
       MIN(p.year) AS first_year,
       MAX(p.year) AS last_year,
       MIN(p.net_profit) AS lowest_net_profit
FROM profitandloss AS p
JOIN companies AS c ON c.company_id = p.company_id
GROUP BY p.company_id, c.company_name, c.sector
HAVING COUNT(DISTINCT p.year) = 12
   AND MIN(p.net_profit) > 0
ORDER BY lowest_net_profit DESC;

-- 9. Referential and annual-data integrity verification.
-- This must return zero rows; any row identifies a financial record lacking a company.
SELECT 'profitandloss' AS table_name, p.company_id, p.year
FROM profitandloss AS p LEFT JOIN companies AS c ON c.company_id = p.company_id
WHERE c.company_id IS NULL
UNION ALL
SELECT 'balancesheet', b.company_id, b.year
FROM balancesheet AS b LEFT JOIN companies AS c ON c.company_id = b.company_id
WHERE c.company_id IS NULL
UNION ALL
SELECT 'cashflow', cf.company_id, cf.year
FROM cashflow AS cf LEFT JOIN companies AS c ON c.company_id = cf.company_id
WHERE c.company_id IS NULL
UNION ALL
SELECT 'source_ratios', sr.company_id, sr.year
FROM source_ratios AS sr LEFT JOIN companies AS c ON c.company_id = sr.company_id
WHERE c.company_id IS NULL;
-- Also run SQLite's native referential-integrity check; it must return zero rows.
PRAGMA foreign_key_check;

-- 10. Summary count of records across all 12 Sprint 1 schema tables.
SELECT 'sectors' AS table_name, COUNT(*) AS record_count FROM sectors
UNION ALL SELECT 'companies', COUNT(*) FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'source_ratios', COUNT(*) FROM source_ratios
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
ORDER BY table_name;

