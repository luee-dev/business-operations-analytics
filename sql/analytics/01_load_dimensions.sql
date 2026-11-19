
-- ============================================================
-- LOAD DIMENSION TABLES
-- 01: CUSTOMERS
-- ============================================================

INSERT INTO analytics.dim_customers (
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
)
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM staging.customers
ON CONFLICT (customer_id)
DO UPDATE SET
    customer_unique_id = EXCLUDED.customer_unique_id,
    customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
    customer_city = EXCLUDED.customer_city,
    customer_state = EXCLUDED.customer_state;


-- ============================================================
-- VALIDATE CUSTOMER DIMENSION
-- ============================================================

SELECT
    COUNT(*) AS customer_count,
    COUNT(DISTINCT customer_id) AS unique_customer_ids,
    COUNT(DISTINCT customer_unique_id) AS unique_customer_entities
FROM analytics.dim_customers;


-- ============================================================
-- 02: PRODUCTS
-- Enrich product categories with English translations.
-- ============================================================

INSERT INTO analytics.dim_products (
    product_id,
    product_category_name,
    product_category_name_english,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    is_product_metadata_incomplete,
    is_physical_measurement_incomplete
)
SELECT
    p.product_id,
    p.product_category_name,
    ct.product_category_name_english,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    p.is_product_metadata_incomplete,
    p.is_physical_measurement_incomplete
FROM staging.products p
LEFT JOIN staging.category_translation ct
    ON p.product_category_name = ct.product_category_name
ON CONFLICT (product_id)
DO UPDATE SET
    product_category_name = EXCLUDED.product_category_name,
    product_category_name_english = EXCLUDED.product_category_name_english,
    product_name_lenght = EXCLUDED.product_name_lenght,
    product_description_lenght = EXCLUDED.product_description_lenght,
    product_photos_qty = EXCLUDED.product_photos_qty,
    product_weight_g = EXCLUDED.product_weight_g,
    product_length_cm = EXCLUDED.product_length_cm,
    product_height_cm = EXCLUDED.product_height_cm,
    product_width_cm = EXCLUDED.product_width_cm,
    is_product_metadata_incomplete = EXCLUDED.is_product_metadata_incomplete,
    is_physical_measurement_incomplete = EXCLUDED.is_physical_measurement_incomplete;


-- ============================================================
-- VALIDATE PRODUCT DIMENSION
-- ============================================================

SELECT
    COUNT(*) AS product_count,
    COUNT(DISTINCT product_id) AS unique_products,
    COUNT(product_category_name_english) AS translated_products,
    COUNT(*) FILTER (
        WHERE is_product_metadata_incomplete
    ) AS incomplete_product_metadata,
    COUNT(*) FILTER (
        WHERE is_physical_measurement_incomplete
    ) AS incomplete_physical_measurements
FROM analytics.dim_products;


-- ============================================================
-- 03: SELLERS
-- ============================================================

INSERT INTO analytics.dim_sellers (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM staging.sellers
ON CONFLICT (seller_id)
DO UPDATE SET
    seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
    seller_city = EXCLUDED.seller_city,
    seller_state = EXCLUDED.seller_state;


-- ============================================================
-- VALIDATE SELLER DIMENSION
-- ============================================================

SELECT
    COUNT(*) AS seller_count,
    COUNT(DISTINCT seller_id) AS unique_sellers,
    COUNT(DISTINCT seller_state) AS states_represented
FROM analytics.dim_sellers;




-- ============================================================
-- 04: DATE DIMENSION
-- Generate one record per calendar date.
-- Include all dates referenced by the fact tables.
-- Date key format: YYYYMMDD
-- ============================================================

WITH date_values AS (

    -- Order dates
    SELECT order_purchase_timestamp::DATE AS event_date
    FROM staging.orders

    UNION ALL

    SELECT order_approved_at::DATE
    FROM staging.orders

    UNION ALL

    SELECT order_delivered_carrier_date::DATE
    FROM staging.orders

    UNION ALL

    SELECT order_delivered_customer_date::DATE
    FROM staging.orders

    UNION ALL

    SELECT order_estimated_delivery_date::DATE
    FROM staging.orders

    -- Order item shipping dates
    UNION ALL

    SELECT shipping_limit_date::DATE
    FROM staging.order_items

    -- Review dates
    UNION ALL

    SELECT review_creation_date::DATE
    FROM staging.reviews

    UNION ALL

    SELECT review_answer_timestamp::DATE
    FROM staging.reviews
),

date_bounds AS (
    SELECT
        MIN(event_date) AS start_date,
        MAX(event_date) AS end_date
    FROM date_values
    WHERE event_date IS NOT NULL
),

calendar AS (
    SELECT
        generated_date::DATE AS calendar_date
    FROM date_bounds,
         generate_series(
             start_date,
             end_date,
             INTERVAL '1 day'
         ) AS generated_date
)

INSERT INTO analytics.dim_date (
    date_key,
    calendar_date,
    calendar_year,
    calendar_quarter,
    month_number,
    month_name,
    day_of_month,
    day_of_week,
    day_name,
    week_of_year,
    is_weekend
)

SELECT
    TO_CHAR(calendar_date, 'YYYYMMDD')::INTEGER AS date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date)::INTEGER,
    EXTRACT(QUARTER FROM calendar_date)::INTEGER,
    EXTRACT(MONTH FROM calendar_date)::INTEGER,
    TO_CHAR(calendar_date, 'FMMonth'),
    EXTRACT(DAY FROM calendar_date)::INTEGER,
    EXTRACT(ISODOW FROM calendar_date)::INTEGER,
    TO_CHAR(calendar_date, 'FMDay'),
    EXTRACT(WEEK FROM calendar_date)::INTEGER,
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7)

FROM calendar

ON CONFLICT (date_key)
DO UPDATE SET
    calendar_date = EXCLUDED.calendar_date,
    calendar_year = EXCLUDED.calendar_year,
    calendar_quarter = EXCLUDED.calendar_quarter,
    month_number = EXCLUDED.month_number,
    month_name = EXCLUDED.month_name,
    day_of_month = EXCLUDED.day_of_month,
    day_of_week = EXCLUDED.day_of_week,
    day_name = EXCLUDED.day_name,
    week_of_year = EXCLUDED.week_of_year,
    is_weekend = EXCLUDED.is_weekend;


-- ============================================================
-- VALIDATE DATE DIMENSION
-- ============================================================

SELECT
    COUNT(*) AS total_calendar_dates,
    MIN(calendar_date) AS first_date,
    MAX(calendar_date) AS last_date,
    COUNT(DISTINCT calendar_date) AS unique_dates,
    COUNT(*) FILTER (
        WHERE is_weekend
    ) AS weekend_dates,
    COUNT(*) FILTER (
        WHERE date_key <> TO_CHAR(calendar_date, 'YYYYMMDD')::INTEGER
    ) AS invalid_date_keys
FROM analytics.dim_date;
