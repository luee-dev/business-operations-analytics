
-- ============================================================
-- LOAD FACT TABLE
-- 01: ORDERS
-- Grain: One row per order
-- ============================================================

INSERT INTO analytics.fact_orders (
    order_id,
    customer_key,
    order_status,

    purchase_date_key,
    approval_date_key,
    carrier_date_key,
    delivery_date_key,
    estimated_delivery_date_key,

    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,

    flag_approval_after_carrier,
    flag_carrier_after_customer_delivery,
    flag_delivered_missing_timestamp
)

SELECT
    o.order_id,
    c.customer_key,
    o.order_status,

    purchase_date.date_key,
    approval_date.date_key,
    carrier_date.date_key,
    delivery_date.date_key,
    estimated_date.date_key,

    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    o.flag_approval_after_carrier,
    o.flag_carrier_after_customer_delivery,
    o.flag_delivered_missing_timestamp

FROM staging.orders o

INNER JOIN analytics.dim_customers c
    ON o.customer_id = c.customer_id

LEFT JOIN analytics.dim_date purchase_date
    ON o.order_purchase_timestamp::DATE = purchase_date.calendar_date

LEFT JOIN analytics.dim_date approval_date
    ON o.order_approved_at::DATE = approval_date.calendar_date

LEFT JOIN analytics.dim_date carrier_date
    ON o.order_delivered_carrier_date::DATE = carrier_date.calendar_date

LEFT JOIN analytics.dim_date delivery_date
    ON o.order_delivered_customer_date::DATE = delivery_date.calendar_date

LEFT JOIN analytics.dim_date estimated_date
    ON o.order_estimated_delivery_date::DATE = estimated_date.calendar_date

ON CONFLICT (order_id)
DO UPDATE SET
    customer_key = EXCLUDED.customer_key,
    order_status = EXCLUDED.order_status,

    purchase_date_key = EXCLUDED.purchase_date_key,
    approval_date_key = EXCLUDED.approval_date_key,
    carrier_date_key = EXCLUDED.carrier_date_key,
    delivery_date_key = EXCLUDED.delivery_date_key,
    estimated_delivery_date_key = EXCLUDED.estimated_delivery_date_key,

    order_purchase_timestamp = EXCLUDED.order_purchase_timestamp,
    order_approved_at = EXCLUDED.order_approved_at,
    order_delivered_carrier_date = EXCLUDED.order_delivered_carrier_date,
    order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
    order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date,

    flag_approval_after_carrier = EXCLUDED.flag_approval_after_carrier,
    flag_carrier_after_customer_delivery = EXCLUDED.flag_carrier_after_customer_delivery,
    flag_delivered_missing_timestamp = EXCLUDED.flag_delivered_missing_timestamp;


-- ============================================================
-- VALIDATE FACT ORDERS
-- ============================================================

SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT order_id) AS unique_orders,
    COUNT(DISTINCT customer_key) AS customers_with_orders,

    COUNT(*) FILTER (
        WHERE purchase_date_key IS NULL
    ) AS missing_purchase_date_keys,

    COUNT(*) FILTER (
        WHERE flag_approval_after_carrier
    ) AS approval_after_carrier_anomalies,

    COUNT(*) FILTER (
        WHERE flag_carrier_after_customer_delivery
    ) AS carrier_after_customer_anomalies,

    COUNT(*) FILTER (
        WHERE flag_delivered_missing_timestamp
    ) AS delivered_missing_timestamp_anomalies

FROM analytics.fact_orders;
