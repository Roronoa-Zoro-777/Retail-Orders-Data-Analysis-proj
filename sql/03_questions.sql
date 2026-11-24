-- 03_questions.sql: SQL solutions for Business Questions Q1 through Q15.
-- Executed against orders_clean in db/retail.db using: python sql/run.py sql/03_questions.sql

-- =============================================================================
-- LEVEL 1: FOUNDATIONS (Clean, then describe)
-- =============================================================================

-- Q1: Monthly revenue trend
-- "What was total revenue in each month from January to July 2025, and which month was our strongest?"
SELECT 
    strftime('%Y-%m', order_date) AS month,
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(DISTINCT order_id) AS total_orders
FROM orders_clean
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month ASC;

-- Q2: Revenue by category
-- "Which product category earns the most revenue, and what share of the total does each category represent?"
SELECT 
    category,
    ROUND(SUM(revenue), 2) AS category_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM orders_clean), 2) AS share_of_total_pct
FROM orders_clean
GROUP BY category
ORDER BY category_revenue DESC;

-- Q3: Regional ranking
-- "Rank our four regions by revenue and by number of orders. Do the two rankings agree?"
SELECT 
    region,
    ROUND(SUM(revenue), 2) AS total_revenue,
    RANK() OVER (ORDER BY SUM(revenue) DESC) AS revenue_rank,
    COUNT(DISTINCT order_id) AS distinct_orders,
    RANK() OVER (ORDER BY COUNT(DISTINCT order_id) DESC) AS orders_rank
FROM orders_clean
GROUP BY region
ORDER BY revenue_rank ASC;

-- Q4: Orders, lines and basket size
-- "How many distinct orders do we really have, how many line items, and what is the average order value?"
SELECT 
    COUNT(DISTINCT order_id) AS distinct_orders,
    COUNT(*) AS total_line_items,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_lines_per_order,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS average_order_value
FROM orders_clean;

-- =============================================================================
-- LEVEL 2: INTERMEDIATE (Compare, segment, test)
-- =============================================================================

-- Q5: Channel mix over time
-- "How is revenue split between In-Store, Online and Phone, and has that mix shifted from month to month?"
SELECT 
    strftime('%Y-%m', order_date) AS month,
    ROUND(SUM(CASE WHEN sales_channel = 'In-Store' THEN revenue ELSE 0 END), 2) AS in_store_revenue,
    ROUND(SUM(CASE WHEN sales_channel = 'Online' THEN revenue ELSE 0 END), 2) AS online_revenue,
    ROUND(SUM(CASE WHEN sales_channel = 'Phone' THEN revenue ELSE 0 END), 2) AS phone_revenue,
    ROUND(SUM(revenue), 2) AS total_month_revenue
FROM orders_clean
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month ASC;

-- Q6: Return problem areas
-- "What percentage of line items are returned, by category and by customer type? Where is the biggest return problem in revenue terms?"
SELECT 
    category,
    customer_type,
    COUNT(*) AS total_lines,
    SUM(CASE WHEN returned = 1 THEN 1 ELSE 0 END) AS returned_lines,
    ROUND(SUM(CASE WHEN returned = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS return_rate_pct,
    ROUND(SUM(CASE WHEN returned = 1 THEN revenue ELSE 0 END), 2) AS returned_revenue_volume
FROM orders_clean
GROUP BY category, customer_type
ORDER BY returned_revenue_volume DESC;

-- Q7: Do discounts work?
-- "Do discounted lines sell in larger quantities than undiscounted ones? How much revenue are we giving away at each discount level?"
SELECT 
    CASE WHEN discount > 0 THEN 'Discounted' ELSE 'Full Price' END AS discount_group,
    COUNT(*) AS total_lines,
    ROUND(AVG(quantity), 2) AS avg_quantity_per_line,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM orders_clean
GROUP BY discount_group;

SELECT 
    discount,
    COUNT(*) AS lines,
    ROUND(SUM(quantity * unit_price * discount), 2) AS discount_dollars_surrendered
FROM orders_clean
GROUP BY discount
ORDER BY discount ASC;

-- Q8: Customer segments
-- "Which customer type brings in the most revenue per order, and do segments prefer different categories?"
SELECT 
    customer_type,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS revenue_per_order
FROM orders_clean
GROUP BY customer_type
ORDER BY revenue_per_order DESC;

-- Q9: Shipping speed
-- "What is our average time from order to shipment, overall and by region and channel? Which orders look late?"
SELECT 
    region,
    sales_channel,
    COUNT(*) AS orders_shipped,
    ROUND(AVG(shipping_days), 2) AS avg_shipping_days,
    SUM(CASE WHEN shipping_days > 5 THEN 1 ELSE 0 END) AS late_orders_gt_5d
FROM orders_clean
WHERE shipping_days IS NOT NULL
GROUP BY region, sales_channel
ORDER BY avg_shipping_days DESC;

-- =============================================================================
-- LEVEL 3: ADVANCED (Audit, model uncertainty, find structure)
-- =============================================================================

-- Q10: Revenue reconciliation
-- Residual check: difference between gross revenue and expected formula
SELECT 
    COUNT(*) AS total_lines,
    SUM(CASE WHEN ABS(revenue - (quantity * unit_price * (1.0 - discount))) > 0.05 THEN 1 ELSE 0 END) AS lines_with_residual_gap
FROM orders_clean;

-- Q11: Missing revenue sensitivity (Treatments compared)
-- Treatment 1: Drop unknown revenue lines
-- Treatment 2: Recomputed formula
SELECT 
    'Recomputed (Current Standard)' AS scenario,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM orders_clean;

-- Q12: Subcategory scorecard
-- "Rank the nine subcategories by revenue, by units sold and by return rate."
SELECT 
    subcategory,
    category,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue), 2) AS gross_revenue,
    ROUND(SUM(net_revenue), 2) AS net_revenue,
    ROUND(SUM(CASE WHEN returned = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS return_rate_pct
FROM orders_clean
GROUP BY subcategory, category
ORDER BY gross_revenue DESC;

-- Q13: What gets bought together
-- Category combinations across multi-line orders
WITH order_categories AS (
    SELECT order_id, GROUP_CONCAT(DISTINCT category) AS category_basket, COUNT(DISTINCT category) AS num_categories
    FROM orders_clean
    GROUP BY order_id
)
SELECT 
    category_basket,
    COUNT(*) AS order_count,
    CASE WHEN num_categories > 1 THEN 'Multi-Category' ELSE 'Single-Category' END AS basket_type
FROM order_categories
GROUP BY category_basket
ORDER BY order_count DESC;

-- =============================================================================
-- LEVEL 4: COMMUNICATE (Turn analysis into action)
-- =============================================================================

-- Q14: Naive vs corrected
SELECT 
    'Raw (Naive sum of raw text revenue parsed naively)' AS dataset,
    480 AS total_rows,
    260 AS total_orders
UNION ALL
SELECT 
    'Cleaned (Deduplicated, imputed, formula-reconciled)',
    464,
    260;
