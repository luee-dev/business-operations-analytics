
-- ============================================================
-- 06: CREATE ORDER PERFORMANCE VIEW
-- Business Operations & Performance Analytics
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_order_performance AS

WITH item_summary AS (
    SELECT
        order_id,
        COUNT(*) AS order_item_count,
        COUNT(DISTINCT product_key) AS distinct_products,
        COUNT(DISTINCT seller_key) AS distinct_sellers,
        SUM(price) AS product_value,
        SUM(freight_value) AS freight_value,
        SUM(price + freight_value) AS expected_order_value
    FROM analytics.fact_order_items
    GROUP BY order_id
),

payment_summary AS (
    SELECT
        order_id,
        COUNT(*) AS payment_count,
        SUM(payment_value) AS payment_value,
        STRING_AGG(
            DISTINCT payment_type,
            ', ' ORDER BY payment_type
        ) AS payment_type,
        MAX(payment_installments) AS payment_installments
    FROM analytics.fact_payments
    GROUP BY order_id
)

SELECT
    -- ========================================================
    -- EXISTING COLUMNS: PRESERVE THEIR ORDER
    -- ========================================================

    o.order_id,
    o.customer_key,
    o.order_status,
    o.purchase_date_key,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,

    COALESCE(i.order_item_count, 0) AS order_item_count,
    COALESCE(i.distinct_products, 0) AS distinct_products,
    COALESCE(i.distinct_sellers, 0) AS distinct_sellers,

    COALESCE(i.product_value, 0) AS product_value,
    COALESCE(i.freight_value, 0) AS freight_value,
    COALESCE(i.expected_order_value, 0) AS expected_order_value,

    COALESCE(p.payment_count, 0) AS payment_count,
    COALESCE(p.payment_value, 0) AS payment_value,
    p.payment_type,
    p.payment_installments,

    CASE
        WHEN i.order_id IS NOT NULL
         AND p.order_id IS NOT NULL
        THEN p.payment_value - i.expected_order_value
        ELSE NULL
    END AS payment_difference,

    o.flag_approval_after_carrier,
    o.flag_carrier_after_customer_delivery,
    o.flag_delivered_missing_timestamp,

    -- ========================================================
    -- NEW COLUMNS: APPENDED AFTER EXISTING COLUMNS
    -- ========================================================

    o.approval_date_key,
    o.carrier_date_key,
    o.delivery_date_key,
    o.estimated_delivery_date_key,

    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_estimated_delivery_date

FROM analytics.fact_orders o

LEFT JOIN item_summary i
    ON o.order_id = i.order_id

LEFT JOIN payment_summary p
    ON o.order_id = p.order_id;
