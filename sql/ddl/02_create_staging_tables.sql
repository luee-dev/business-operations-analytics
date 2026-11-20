
-- =========================================================
-- BUSINESS OPERATIONS ANALYTICS
-- STAGING LAYER TABLE DEFINITIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city TEXT,
    customer_state VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS staging.geolocation (
    geolocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city TEXT,
    geolocation_state VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ,

    flag_approval_after_carrier BOOLEAN NOT NULL DEFAULT FALSE,
    flag_carrier_after_customer_delivery BOOLEAN NOT NULL DEFAULT FALSE,
    flag_delivered_missing_timestamp BOOLEAN NOT NULL DEFAULT FALSE,

    is_delivered_timestamp_missing BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12,2),
    product_length_cm NUMERIC(12,2),
    product_height_cm NUMERIC(12,2),
    product_width_cm NUMERIC(12,2),

    is_product_metadata_incomplete BOOLEAN NOT NULL DEFAULT FALSE,
    is_physical_measurement_incomplete BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS staging.sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT,
    seller_state VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMPTZ,
    price NUMERIC(12,2) NOT NULL,
    freight_value NUMERIC(12,2) NOT NULL,

    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS staging.payments (
    order_id VARCHAR(50) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(30),
    payment_installments INTEGER,
    payment_value NUMERIC(12,2) NOT NULL,

    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS staging.reviews (
    staging_review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    review_score SMALLINT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMPTZ,
    review_answer_timestamp TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_staging_reviews_review_id
ON staging.reviews (review_id);

CREATE INDEX IF NOT EXISTS idx_staging_reviews_order_id
ON staging.reviews (order_id);

CREATE TABLE IF NOT EXISTS staging.category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
