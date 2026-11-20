
-- ============================================================
-- BUSINESS OPERATIONS & PERFORMANCE ANALYTICS
-- Analytics Layer: Star Schema
-- File: 03_create_analytics_tables.sql
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. DIMENSION TABLES
-- ============================================================

-- ------------------------------------------------------------
-- DIM_DATE
-- One row per calendar date.
-- Date key format: YYYYMMDD
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INTEGER PRIMARY KEY,
    calendar_date DATE NOT NULL UNIQUE,
    calendar_year INTEGER NOT NULL,
    calendar_quarter INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,

    CONSTRAINT chk_dim_date_quarter
        CHECK (calendar_quarter BETWEEN 1 AND 4),

    CONSTRAINT chk_dim_date_month
        CHECK (month_number BETWEEN 1 AND 12),

    CONSTRAINT chk_dim_date_day
        CHECK (day_of_month BETWEEN 1 AND 31)
);


-- ------------------------------------------------------------
-- DIM_CUSTOMERS
-- One row per customer_id.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.dim_customers (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix INTEGER,
    customer_city TEXT,
    customer_state VARCHAR(2)
);


-- ------------------------------------------------------------
-- DIM_PRODUCTS
-- One row per product.
-- Includes English category translation where available.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.dim_products (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL UNIQUE,
    product_category_name TEXT,
    product_category_name_english TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12,2),
    product_length_cm NUMERIC(12,2),
    product_height_cm NUMERIC(12,2),
    product_width_cm NUMERIC(12,2),
    is_product_metadata_incomplete BOOLEAN NOT NULL,
    is_physical_measurement_incomplete BOOLEAN NOT NULL
);


-- ------------------------------------------------------------
-- DIM_SELLERS
-- One row per seller.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.dim_sellers (
    seller_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id VARCHAR(50) NOT NULL UNIQUE,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT,
    seller_state VARCHAR(2)
);


-- ============================================================
-- 2. FACT TABLES
-- ============================================================

-- ------------------------------------------------------------
-- FACT_ORDERS
-- Grain: one row per order.
-- Financial amounts are deliberately excluded here.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.fact_orders (
    order_id VARCHAR(50) PRIMARY KEY,

    customer_key BIGINT NOT NULL
        REFERENCES analytics.dim_customers(customer_key),

    order_status VARCHAR(30) NOT NULL,

    purchase_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    approval_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    carrier_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    delivery_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    estimated_delivery_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    order_purchase_timestamp TIMESTAMPTZ,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ,

    flag_approval_after_carrier BOOLEAN NOT NULL,
    flag_carrier_after_customer_delivery BOOLEAN NOT NULL,
    flag_delivered_missing_timestamp BOOLEAN NOT NULL
);


-- ------------------------------------------------------------
-- FACT_ORDER_ITEMS
-- Grain: one row per order item.
-- Contains product price and freight value.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.fact_order_items (
    order_item_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_id VARCHAR(50) NOT NULL
        REFERENCES analytics.fact_orders(order_id),

    order_item_id INTEGER NOT NULL,

    product_key BIGINT NOT NULL
        REFERENCES analytics.dim_products(product_key),

    seller_key BIGINT NOT NULL
        REFERENCES analytics.dim_sellers(seller_key),

    shipping_limit_date TIMESTAMPTZ,

    shipping_limit_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    price NUMERIC(12,2) NOT NULL,
    freight_value NUMERIC(12,2) NOT NULL,

    CONSTRAINT uq_fact_order_items
        UNIQUE (order_id, order_item_id),

    CONSTRAINT chk_fact_item_price
        CHECK (price >= 0),

    CONSTRAINT chk_fact_freight_value
        CHECK (freight_value >= 0)
);


-- ------------------------------------------------------------
-- FACT_PAYMENTS
-- Grain: one row per payment sequence within an order.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.fact_payments (
    payment_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_id VARCHAR(50) NOT NULL
        REFERENCES analytics.fact_orders(order_id),

    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(30),
    payment_installments INTEGER,
    payment_value NUMERIC(12,2) NOT NULL,

    CONSTRAINT uq_fact_payments
        UNIQUE (order_id, payment_sequential),

    CONSTRAINT chk_fact_payment_value
        CHECK (payment_value >= 0)
);


-- ------------------------------------------------------------
-- FACT_REVIEWS
-- Grain: one row per staging review record.
-- review_id is NOT assumed to be unique.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.fact_reviews (
    review_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    staging_review_id BIGINT NOT NULL UNIQUE,
    review_id VARCHAR(50) NOT NULL,

    order_id VARCHAR(50) NOT NULL
        REFERENCES analytics.fact_orders(order_id),

    review_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    answer_date_key INTEGER
        REFERENCES analytics.dim_date(date_key),

    review_score SMALLINT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMPTZ,
    review_answer_timestamp TIMESTAMPTZ,

    CONSTRAINT chk_fact_review_score
        CHECK (review_score BETWEEN 1 AND 5 OR review_score IS NULL)
);


-- ============================================================
-- 3. INDEXES
-- Improve common filtering and joining operations.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer
    ON analytics.fact_orders(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_orders_status
    ON analytics.fact_orders(order_status);

CREATE INDEX IF NOT EXISTS idx_fact_orders_purchase_date
    ON analytics.fact_orders(purchase_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_product
    ON analytics.fact_order_items(product_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_seller
    ON analytics.fact_order_items(seller_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_order
    ON analytics.fact_order_items(order_id);

CREATE INDEX IF NOT EXISTS idx_fact_payments_order
    ON analytics.fact_payments(order_id);

CREATE INDEX IF NOT EXISTS idx_fact_payments_type
    ON analytics.fact_payments(payment_type);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_order
    ON analytics.fact_reviews(order_id);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_score
    ON analytics.fact_reviews(review_score);


-- ============================================================
-- END OF ANALYTICS TABLE DEFINITIONS
-- ============================================================
