-- 01_audit.sql: SQL queries to audit the raw dataset in orders_raw.
-- Run using: python sql/run.py sql/01_audit.sql
-- Write queries to verify each issue identified in the workbook.

-- =============================================================================
-- 1. Exact Duplicate Rows
-- Target: 16 rows are exact copies of another row
-- TODO: Group by all 15 columns and find rows where COUNT(*) > 1.
-- =============================================================================
-- SELECT order_id, order_date, ... COUNT(*) FROM orders_raw GROUP BY ... HAVING COUNT(*) > 1;


-- =============================================================================
-- 2. Repeated order_id & Table Grain
-- Target: Only 260 unique order IDs across 480 rows
-- TODO: Count distinct order_ids and count occurrences per order_id.
-- =============================================================================
-- SELECT COUNT(DISTINCT order_id), COUNT(*) FROM orders_raw;


-- =============================================================================
-- 3. Date Formats & Placeholders
-- Target: order_date mixes 4 formats + 6 unparseable; ship_date mixes 4 formats + 4 'TBD'
-- TODO: Inspect non-standard date patterns and placeholder text.
-- =============================================================================
-- SELECT order_date, COUNT(*) FROM orders_raw GROUP BY order_date ORDER BY COUNT(*) DESC;


-- =============================================================================
-- 4. Categorical Inconsistent Labels
-- Targets:
--   region: 21 distinct values (4 intended)
--   city: 40 distinct values (16 intended)
--   category: 17 distinct values (3 intended)
--   sales_channel: 16 distinct values
--   customer_type: 12 distinct values
-- TODO: Inspect distinct values and frequencies for each categorical column.
-- =============================================================================
-- SELECT region, COUNT(*) FROM orders_raw GROUP BY region;
-- SELECT category, COUNT(*) FROM orders_raw GROUP BY category;


-- =============================================================================
-- 5. Numbers Stored as Text
-- Targets:
--   quantity: words ("two"), suffixes ("3 units"), whitespace
--   unit_price: "$", "USD", commas, whitespace
--   revenue: "$", "USD", commas, whitespace, negative signs
-- TODO: Find rows containing non-numeric characters.
-- =============================================================================


-- =============================================================================
-- 6. Negative and Bracketed Revenue
-- Target: Values written as -$37.30 or (103.75)
-- TODO: Identify all rows with negative or parenthesized revenue.
-- =============================================================================


-- =============================================================================
-- 7. Discount Formats
-- Target: 25 different spellings (0.10, .10, 10%, '10 percent', none, 'No discount', blank)
-- TODO: List all distinct discount values and counts.
-- =============================================================================
-- SELECT discount, COUNT(*) FROM orders_raw GROUP BY discount;


-- =============================================================================
-- 8. Return Flag Coding
-- Target: 14 different codes for yes / no / unknown
-- TODO: List all distinct returned values and counts.
-- =============================================================================
-- SELECT returned, COUNT(*) FROM orders_raw GROUP BY returned;


-- =============================================================================
-- 9. Missing-Value Codes
-- Target: blank, '.', em dash '—', 'unknown', 'TBD', 'not recorded', 'none'
-- TODO: Count occurrences of each placeholder across columns.
-- =============================================================================


-- =============================================================================
-- 10. Potential Internal Inconsistencies
-- Target: revenue vs quantity * unit_price * (1 - discount)
-- TODO: Write check to compare calculated vs recorded revenue.
-- =============================================================================
