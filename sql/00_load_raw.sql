-- 00_load_raw.sql: Table definition for raw retail orders dataset.
-- Every column is stored as TEXT so no values are silently altered or coerced.

DROP TABLE IF EXISTS orders_raw;

CREATE TABLE orders_raw (
    order_id TEXT,
    order_date TEXT,
    ship_date TEXT,
    region TEXT,
    city TEXT,
    category TEXT,
    subcategory TEXT,
    sales_channel TEXT,
    customer_type TEXT,
    quantity TEXT,
    unit_price TEXT,
    discount TEXT,
    revenue TEXT,
    returned TEXT,
    notes TEXT
);
