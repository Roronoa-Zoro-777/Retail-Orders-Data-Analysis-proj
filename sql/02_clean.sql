-- 02_clean.sql: Verification and inspection of the cleaned dataset in orders_clean.
-- Run using: python sql/run.py sql/02_clean.sql

SELECT 
    COUNT(*) AS total_clean_rows,
    COUNT(DISTINCT order_id) AS distinct_orders,
    ROUND(SUM(revenue), 2) AS total_gross_revenue,
    ROUND(SUM(net_revenue), 2) AS total_net_revenue,
    SUM(CASE WHEN returned = 1 THEN 1 ELSE 0 END) AS returned_lines
FROM orders_clean;

-- Verification of categorical consistency:
SELECT region, COUNT(*) AS row_count, ROUND(SUM(revenue), 2) AS revenue
FROM orders_clean
GROUP BY region
ORDER BY revenue DESC;

SELECT category, COUNT(*) AS row_count, ROUND(SUM(revenue), 2) AS revenue
FROM orders_clean
GROUP BY category
ORDER BY revenue DESC;
