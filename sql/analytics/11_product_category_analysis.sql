
-- ============================================================
-- 11. PRODUCT AND CATEGORY PERFORMANCE ANALYSIS
-- Project: Business Operations & Performance Analytics
--
-- Grain:
--   vw_product_performance  : one row per catalogue product
--   vw_category_performance : one row per product category
--
-- Commercial performance is measured primarily using
-- delivered orders. Canceled and other statuses are retained
-- separately for operational analysis.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. PRODUCT PERFORMANCE
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_product_performance AS

WITH product_catalog AS (
    SELECT
        product_key,
        product_id,

        COALESCE(
            NULLIF(BTRIM(product_category_name_english), ''),
            NULLIF(BTRIM(product_category_name), ''),
            'uncategorized'
        ) AS product_category,

        product_name_lenght,
        product_description_lenght,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        is_product_metadata_incomplete,
        is_physical_measurement_incomplete

    FROM analytics.dim_products
),

product_item_metrics AS (
    SELECT
        foi.product_key,

        COUNT(*) AS total_order_item_lines,

        COUNT(DISTINCT foi.order_id) AS total_orders,

        COUNT(DISTINCT foi.seller_key) AS distinct_sellers,

        COUNT(*) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_orders,

        COUNT(*) FILTER (
            WHERE fo.order_status NOT IN ('delivered', 'canceled')
        ) AS other_status_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status NOT IN ('delivered', 'canceled')
        ) AS other_status_orders,

        SUM(foi.price) AS total_product_value,

        SUM(foi.price) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_product_value,

        SUM(foi.price) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_product_value,

        SUM(foi.freight_value) AS total_freight_value,

        SUM(foi.freight_value) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_freight_value,

        AVG(foi.price) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS average_delivered_item_price

    FROM analytics.fact_order_items foi

    INNER JOIN analytics.fact_orders fo
        ON foi.order_id = fo.order_id

    GROUP BY foi.product_key
)

SELECT
    pc.product_key,
    pc.product_id,
    pc.product_category,

    pc.product_name_lenght,
    pc.product_description_lenght,
    pc.product_photos_qty,

    pc.product_weight_g,
    pc.product_length_cm,
    pc.product_height_cm,
    pc.product_width_cm,

    pc.is_product_metadata_incomplete,
    pc.is_physical_measurement_incomplete,

    COALESCE(pm.total_order_item_lines, 0)
        AS total_order_item_lines,

    COALESCE(pm.total_orders, 0)
        AS total_orders,

    COALESCE(pm.distinct_sellers, 0)
        AS distinct_sellers,

    COALESCE(pm.delivered_item_lines, 0)
        AS delivered_item_lines,

    COALESCE(pm.delivered_orders, 0)
        AS delivered_orders,

    COALESCE(pm.canceled_item_lines, 0)
        AS canceled_item_lines,

    COALESCE(pm.canceled_orders, 0)
        AS canceled_orders,

    COALESCE(pm.other_status_item_lines, 0)
        AS other_status_item_lines,

    COALESCE(pm.other_status_orders, 0)
        AS other_status_orders,

    COALESCE(pm.total_product_value, 0)
        AS total_product_value,

    COALESCE(pm.delivered_product_value, 0)
        AS delivered_product_value,

    COALESCE(pm.canceled_product_value, 0)
        AS canceled_product_value,

    COALESCE(pm.total_freight_value, 0)
        AS total_freight_value,

    COALESCE(pm.delivered_freight_value, 0)
        AS delivered_freight_value,

    COALESCE(pm.average_delivered_item_price, 0)
        AS average_delivered_item_price

FROM product_catalog pc

LEFT JOIN product_item_metrics pm
    ON pc.product_key = pm.product_key;


-- ------------------------------------------------------------
-- 2. CATEGORY PERFORMANCE
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_category_performance AS

WITH category_catalog AS (
    SELECT
        product_category,

        COUNT(*) AS total_products,

        COUNT(*) FILTER (
            WHERE is_product_metadata_incomplete = TRUE
        ) AS products_with_incomplete_metadata,

        COUNT(*) FILTER (
            WHERE is_physical_measurement_incomplete = TRUE
        ) AS products_with_incomplete_physical_measurements

    FROM analytics.vw_product_performance

    GROUP BY product_category
),

category_item_metrics AS (
    SELECT
        COALESCE(
            NULLIF(BTRIM(dp.product_category_name_english), ''),
            NULLIF(BTRIM(dp.product_category_name), ''),
            'uncategorized'
        ) AS product_category,

        COUNT(*) AS total_order_item_lines,

        COUNT(DISTINCT foi.order_id) AS total_orders,

        COUNT(DISTINCT foi.seller_key) AS distinct_sellers,

        COUNT(*) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_orders,

        COUNT(*) FILTER (
            WHERE fo.order_status NOT IN ('delivered', 'canceled')
        ) AS other_status_item_lines,

        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.order_status NOT IN ('delivered', 'canceled')
        ) AS other_status_orders,

        SUM(foi.price) AS total_product_value,

        SUM(foi.price) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_product_value,

        SUM(foi.price) FILTER (
            WHERE fo.order_status = 'canceled'
        ) AS canceled_product_value,

        SUM(foi.freight_value) AS total_freight_value,

        SUM(foi.freight_value) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS delivered_freight_value,

        AVG(foi.price) FILTER (
            WHERE fo.order_status = 'delivered'
        ) AS average_delivered_item_price

    FROM analytics.fact_order_items foi

    INNER JOIN analytics.fact_orders fo
        ON foi.order_id = fo.order_id

    INNER JOIN analytics.dim_products dp
        ON foi.product_key = dp.product_key

    GROUP BY
        COALESCE(
            NULLIF(BTRIM(dp.product_category_name_english), ''),
            NULLIF(BTRIM(dp.product_category_name), ''),
            'uncategorized'
        )
),

category_results AS (
    SELECT
        cc.product_category,

        cc.total_products,

        cc.products_with_incomplete_metadata,

        cc.products_with_incomplete_physical_measurements,

        COALESCE(cm.total_order_item_lines, 0)
            AS total_order_item_lines,

        COALESCE(cm.total_orders, 0)
            AS total_orders,

        COALESCE(cm.distinct_sellers, 0)
            AS distinct_sellers,

        COALESCE(cm.delivered_item_lines, 0)
            AS delivered_item_lines,

        COALESCE(cm.delivered_orders, 0)
            AS delivered_orders,

        COALESCE(cm.canceled_item_lines, 0)
            AS canceled_item_lines,

        COALESCE(cm.canceled_orders, 0)
            AS canceled_orders,

        COALESCE(cm.other_status_item_lines, 0)
            AS other_status_item_lines,

        COALESCE(cm.other_status_orders, 0)
            AS other_status_orders,

        COALESCE(cm.total_product_value, 0)
            AS total_product_value,

        COALESCE(cm.delivered_product_value, 0)
            AS delivered_product_value,

        COALESCE(cm.canceled_product_value, 0)
            AS canceled_product_value,

        COALESCE(cm.total_freight_value, 0)
            AS total_freight_value,

        COALESCE(cm.delivered_freight_value, 0)
            AS delivered_freight_value,

        COALESCE(cm.average_delivered_item_price, 0)
            AS average_delivered_item_price

    FROM category_catalog cc

    LEFT JOIN category_item_metrics cm
        ON cc.product_category = cm.product_category
)

SELECT
    *,

    ROUND(
        100.0 * delivered_product_value
        / NULLIF(
            SUM(delivered_product_value) OVER (),
            0
        ),
        2
    ) AS delivered_sales_share_percentage,

    ROUND(
        100.0 * delivered_orders
        / NULLIF(total_orders, 0),
        2
    ) AS delivered_order_percentage,

    ROUND(
        100.0 * canceled_orders
        / NULLIF(total_orders, 0),
        2
    ) AS canceled_order_percentage

FROM category_results;


COMMIT;