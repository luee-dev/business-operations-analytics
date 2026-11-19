
-- =========================================================
-- BUSINESS OPERATIONS ANALYTICS
-- RAW LAYER TABLE DEFINITIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS raw.customers (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id TEXT,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.geolocation (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geolocation_zip_code_prefix TEXT,
    geolocation_lat TEXT,
    geolocation_lng TEXT,
    geolocation_city TEXT,
    geolocation_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT,
    order_item_id TEXT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price TEXT,
    freight_value TEXT
);

CREATE TABLE IF NOT EXISTS raw.payments (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT,
    payment_sequential TEXT,
    payment_type TEXT,
    payment_installments TEXT,
    payment_value TEXT
);

CREATE TABLE IF NOT EXISTS raw.reviews (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id TEXT,
    order_id TEXT,
    review_score TEXT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT
);

CREATE TABLE IF NOT EXISTS raw.orders (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TEXT,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT
);

CREATE TABLE IF NOT EXISTS raw.products (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id TEXT,
    product_category_name TEXT,
    product_name_lenght TEXT,
    product_description_lenght TEXT,
    product_photos_qty TEXT,
    product_weight_g TEXT,
    product_length_cm TEXT,
    product_height_cm TEXT,
    product_width_cm TEXT
);

CREATE TABLE IF NOT EXISTS raw.sellers (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id TEXT,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.category_translation (
    raw_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_category_name TEXT,
    product_category_name_english TEXT
);
