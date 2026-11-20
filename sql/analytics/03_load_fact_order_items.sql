
-- ============================================================
-- LOAD FACT TABLE
-- 02: ORDER ITEMS
-- Grain: One row per order item
-- Natural key: (order_id, order_item_id)
-- ============================================================

INSERT INTO analytics.fact_order_items (
    order_id,
    order_item_id,
    product_key,
    seller_key,
    shipping_limit_date,
    shipping_limit_date_key,
    price,
    freight_value
)

SELECT
    oi.order_id,
    oi.order_item_id,
    p.product_key,
    s.seller_key,
    oi.shipping_limit_date,
    d.date_key AS shipping_limit_date_key,
    oi.price,
    oi.freight_value

FROM staging.order_items oi

INNER JOIN analytics.dim_products p
    ON oi.product_id = p.product_id

INNER JOIN analytics.dim_sellers s
    ON oi.seller_id = s.seller_id

LEFT JOIN analytics.dim_date d
    ON oi.shipping_limit_date::DATE = d.calendar_date

ON CONFLICT (order_id, order_item_id)
DO UPDATE SET
    product_key = EXCLUDED.product_key,
    seller_key = EXCLUDED.seller_key,
    shipping_limit_date = EXCLUDED.shipping_limit_date,
    shipping_limit_date_key = EXCLUDED.shipping_limit_date_key,
    price = EXCLUDED.price,
    freight_value = EXCLUDED.freight_value;


-- ============================================================
-- VALIDATE FACT ORDER ITEMS
-- ============================================================

SELECT
    COUNT(*) AS total_order_items,

    COUNT(DISTINCT (order_id, order_item_id))
        AS unique_order_items,

    COUNT(DISTINCT order_id)
        AS orders_with_items,

    COUNT(DISTINCT product_key)
        AS products_sold,

    COUNT(DISTINCT seller_key)
        AS sellers_involved,

    COUNT(*) FILTER (
        WHERE shipping_limit_date_key IS NULL
    ) AS missing_shipping_date_keys,

    SUM(price) AS total_item_revenue,

    SUM(freight_value) AS total_freight_value,

    COUNT(*) FILTER (
        WHERE price < 0
    ) AS negative_prices,

    COUNT(*) FILTER (
        WHERE freight_value < 0
    ) AS negative_freight_values

FROM analytics.fact_order_items;
