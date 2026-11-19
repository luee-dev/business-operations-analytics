
-- ============================================================
-- 12. SELLER PERFORMANCE AND OPERATIONAL ANALYSIS
-- Business Operations & Performance Analytics Platform
--
-- Grain:
--   One row per seller in vw_seller_performance.
--
-- Important:
--   Order counts are seller-order associations. An order with
--   multiple sellers contributes once to each associated seller.
--   Do not sum seller order counts and interpret the result as
--   distinct marketplace orders.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Seller-order level dataset
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_seller_order_performance AS

SELECT
    foi.seller_key,
    foi.order_id,

    fo.customer_key,
    fo.order_status,

    COUNT(*) AS item_lines,

    COUNT(DISTINCT foi.product_key) AS distinct_products,

    SUM(foi.price) AS product_value,
    SUM(foi.freight_value) AS freight_value,

    COUNT(*) FILTER (
        WHERE foi.shipping_limit_date IS NOT NULL
          AND fo.order_delivered_carrier_date IS NOT NULL
    ) AS shipping_deadline_eligible_item_lines,

    COUNT(*) FILTER (
        WHERE foi.shipping_limit_date IS NOT NULL
          AND fo.order_delivered_carrier_date IS NOT NULL
          AND fo.order_delivered_carrier_date > foi.shipping_limit_date
    ) AS shipping_deadline_late_item_lines,

    CASE
        WHEN fo.order_status = 'delivered'
         AND fo.order_delivered_carrier_date IS NOT NULL
         AND fo.order_purchase_timestamp IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                fo.order_delivered_carrier_date
                - fo.order_purchase_timestamp
            )
        ) / 86400.0
    END AS purchase_to_carrier_days,

    CASE
        WHEN fo.order_status = 'delivered'
         AND fo.order_delivered_carrier_date IS NOT NULL
         AND fo.order_delivered_customer_date IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                fo.order_delivered_customer_date
                - fo.order_delivered_carrier_date
            )
        ) / 86400.0
    END AS carrier_to_customer_days,

    CASE
        WHEN fo.order_status = 'delivered'
         AND fo.order_purchase_timestamp IS NOT NULL
         AND fo.order_delivered_customer_date IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                fo.order_delivered_customer_date
                - fo.order_purchase_timestamp
            )
        ) / 86400.0
    END AS total_delivery_days,

    CASE
        WHEN fo.order_status = 'delivered'
         AND fo.order_delivered_customer_date IS NOT NULL
         AND fo.order_estimated_delivery_date IS NOT NULL
        THEN fo.order_delivered_customer_date
             > fo.order_estimated_delivery_date
    END AS is_late_delivery

FROM analytics.fact_order_items foi

INNER JOIN analytics.fact_orders fo
    ON foi.order_id = fo.order_id

GROUP BY
    foi.seller_key,
    foi.order_id,
    fo.customer_key,
    fo.order_status,
    fo.order_purchase_timestamp,
    fo.order_delivered_carrier_date,
    fo.order_delivered_customer_date,
    fo.order_estimated_delivery_date;


-- ------------------------------------------------------------
-- 2. Seller-level performance
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_seller_performance AS

WITH seller_summary AS (

    SELECT
        seller_key,

        COUNT(*) AS total_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'canceled'
        ) AS canceled_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'shipped'
        ) AS shipped_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'invoiced'
        ) AS invoiced_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'processing'
        ) AS processing_order_associations,

        COUNT(*) FILTER (
            WHERE order_status = 'unavailable'
        ) AS unavailable_order_associations,

        COUNT(*) FILTER (
            WHERE order_status NOT IN (
                'delivered',
                'canceled',
                'shipped',
                'invoiced',
                'processing',
                'unavailable'
            )
        ) AS other_order_associations,

        SUM(item_lines) AS total_item_lines,

        SUM(item_lines) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_item_lines,

        COUNT(DISTINCT customer_key) AS distinct_customers,

        SUM(product_value) AS total_product_value,

        SUM(product_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_product_value,

        SUM(freight_value) AS total_freight_value,

        SUM(freight_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_freight_value,

        AVG(product_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS average_delivered_order_value,

        COUNT(*) FILTER (
            WHERE is_late_delivery IS NOT NULL
        ) AS delivery_estimate_eligible_orders,

        COUNT(*) FILTER (
            WHERE is_late_delivery IS TRUE
        ) AS late_delivery_order_associations,

        COUNT(*) FILTER (
            WHERE is_late_delivery IS FALSE
        ) AS on_time_delivery_order_associations,

        COUNT(*) FILTER (
            WHERE shipping_deadline_eligible_item_lines > 0
        ) AS shipping_deadline_eligible_order_associations,

        SUM(shipping_deadline_eligible_item_lines)
            AS shipping_deadline_eligible_item_lines,

        SUM(shipping_deadline_late_item_lines)
            AS shipping_deadline_late_item_lines,

        AVG(purchase_to_carrier_days) AS avg_purchase_to_carrier_days,

        AVG(carrier_to_customer_days) AS avg_carrier_to_customer_days,

        AVG(total_delivery_days) AS avg_total_delivery_days,

        PERCENTILE_CONT(0.50)
            WITHIN GROUP (ORDER BY total_delivery_days)
            FILTER (WHERE total_delivery_days IS NOT NULL)
            AS median_total_delivery_days,

        PERCENTILE_CONT(0.90)
            WITHIN GROUP (ORDER BY total_delivery_days)
            FILTER (WHERE total_delivery_days IS NOT NULL)
            AS p90_total_delivery_days

    FROM analytics.vw_seller_order_performance

    GROUP BY seller_key
),

seller_products AS (

    SELECT
        seller_key,
        COUNT(DISTINCT product_key) AS distinct_products_sold

    FROM analytics.fact_order_items

    GROUP BY seller_key
),

combined AS (

    SELECT
        ds.seller_key,
        ds.seller_id,
        ds.seller_city,
        ds.seller_state,
        ds.seller_zip_code_prefix,

        COALESCE(ss.total_order_associations, 0)
            AS total_order_associations,

        COALESCE(ss.delivered_order_associations, 0)
            AS delivered_order_associations,

        COALESCE(ss.canceled_order_associations, 0)
            AS canceled_order_associations,

        COALESCE(ss.shipped_order_associations, 0)
            AS shipped_order_associations,

        COALESCE(ss.invoiced_order_associations, 0)
            AS invoiced_order_associations,

        COALESCE(ss.processing_order_associations, 0)
            AS processing_order_associations,

        COALESCE(ss.unavailable_order_associations, 0)
            AS unavailable_order_associations,

        COALESCE(ss.other_order_associations, 0)
            AS other_order_associations,

        COALESCE(ss.total_item_lines, 0)
            AS total_item_lines,

        COALESCE(ss.delivered_item_lines, 0)
            AS delivered_item_lines,

        COALESCE(ss.distinct_customers, 0)
            AS distinct_customers,

        COALESCE(sp.distinct_products_sold, 0)
            AS distinct_products_sold,

        COALESCE(ss.total_product_value, 0)
            AS total_product_value,

        COALESCE(ss.delivered_product_value, 0)
            AS delivered_product_value,

        COALESCE(ss.total_freight_value, 0)
            AS total_freight_value,

        COALESCE(ss.delivered_freight_value, 0)
            AS delivered_freight_value,

        ss.average_delivered_order_value,

        COALESCE(ss.delivery_estimate_eligible_orders, 0)
            AS delivery_estimate_eligible_orders,

        COALESCE(ss.late_delivery_order_associations, 0)
            AS late_delivery_order_associations,

        COALESCE(ss.on_time_delivery_order_associations, 0)
            AS on_time_delivery_order_associations,

        COALESCE(ss.shipping_deadline_eligible_order_associations, 0)
            AS shipping_deadline_eligible_order_associations,

        COALESCE(ss.shipping_deadline_eligible_item_lines, 0)
            AS shipping_deadline_eligible_item_lines,

        COALESCE(ss.shipping_deadline_late_item_lines, 0)
            AS shipping_deadline_late_item_lines,

        ss.avg_purchase_to_carrier_days,
        ss.avg_carrier_to_customer_days,
        ss.avg_total_delivery_days,
        ss.median_total_delivery_days,
        ss.p90_total_delivery_days

    FROM analytics.dim_sellers ds

    LEFT JOIN seller_summary ss
        ON ds.seller_key = ss.seller_key

    LEFT JOIN seller_products sp
        ON ds.seller_key = sp.seller_key
)

SELECT
    *,

    ROUND(
        100.0 * delivered_order_associations
        / NULLIF(total_order_associations, 0),
        2
    ) AS delivered_order_percentage,

    ROUND(
        100.0 * canceled_order_associations
        / NULLIF(total_order_associations, 0),
        2
    ) AS canceled_order_percentage,

    ROUND(
        100.0 * late_delivery_order_associations
        / NULLIF(delivery_estimate_eligible_orders, 0),
        2
    ) AS late_delivery_percentage,

    ROUND(
        100.0 * on_time_delivery_order_associations
        / NULLIF(delivery_estimate_eligible_orders, 0),
        2
    ) AS on_time_delivery_percentage,

    ROUND(
        100.0 * shipping_deadline_late_item_lines
        / NULLIF(shipping_deadline_eligible_item_lines, 0),
        2
    ) AS shipping_deadline_late_percentage,

    ROUND(
        delivered_product_value
        / NULLIF(delivered_order_associations, 0),
        2
    ) AS delivered_value_per_order_association,

    DENSE_RANK() OVER (
        ORDER BY delivered_product_value DESC
    ) AS delivered_sales_rank

FROM combined;
