
-- ============================================================
-- 13. CROSS-FUNCTIONAL BUSINESS ANALYSIS
-- Business Operations & Performance Analytics Platform
--
-- Purpose:
-- Connect delivery, customer satisfaction, payment behaviour,
-- customer segments, product categories and seller performance.
--
-- Grain management:
--   Reviews are aggregated to order level before joining.
--   Payment information comes from the existing order view.
--   Product and seller analyses use item-level facts.
--   Customer segment analysis uses customer_unique_id.
-- ============================================================


-- ------------------------------------------------------------
-- VIEW 1: Order-level delivery and customer review performance
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_order_review_performance AS

WITH review_summary AS (

    SELECT
        order_id,

        COUNT(*) AS review_records,

        COUNT(review_score) AS scored_review_records,

        ROUND(
            AVG(review_score)::numeric,
            2
        ) AS average_review_score,

        COUNT(*) FILTER (
            WHERE review_score <= 2
        ) AS negative_review_records,

        COUNT(*) FILTER (
            WHERE review_score = 3
        ) AS neutral_review_records,

        COUNT(*) FILTER (
            WHERE review_score >= 4
        ) AS positive_review_records

    FROM analytics.fact_reviews

    GROUP BY order_id
)

SELECT
    op.order_id,
    op.customer_key,
    op.order_status,

    op.order_purchase_timestamp,
    op.order_delivered_customer_date,
    op.order_estimated_delivery_date,

    op.order_item_count,
    op.distinct_products,
    op.distinct_sellers,

    op.product_value,
    op.freight_value,
    op.expected_order_value,

    COALESCE(rs.review_records, 0) AS review_records,

    COALESCE(rs.scored_review_records, 0)
        AS scored_review_records,

    rs.average_review_score,

    COALESCE(rs.negative_review_records, 0)
        AS negative_review_records,

    COALESCE(rs.neutral_review_records, 0)
        AS neutral_review_records,

    COALESCE(rs.positive_review_records, 0)
        AS positive_review_records,

    CASE
        WHEN op.order_status = 'delivered'
         AND op.order_delivered_customer_date IS NOT NULL
         AND op.order_estimated_delivery_date IS NOT NULL
        THEN op.order_delivered_customer_date
             > op.order_estimated_delivery_date
    END AS is_late_delivery,

    CASE
        WHEN op.order_status = 'delivered'
         AND op.order_delivered_customer_date IS NOT NULL
         AND op.order_purchase_timestamp IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                op.order_delivered_customer_date
                - op.order_purchase_timestamp
            )
        ) / 86400.0
    END AS delivery_days,

    CASE
        WHEN op.order_status = 'delivered'
         AND op.order_delivered_customer_date IS NOT NULL
         AND op.order_estimated_delivery_date IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                op.order_delivered_customer_date
                - op.order_estimated_delivery_date
            )
        ) / 86400.0
    END AS delivery_variance_days

FROM analytics.vw_order_performance op

LEFT JOIN review_summary rs
    ON op.order_id = rs.order_id;


-- ------------------------------------------------------------
-- VIEW 2: Delivery performance and customer satisfaction
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_delivery_review_analysis AS

SELECT
    CASE
        WHEN is_late_delivery IS TRUE
            THEN 'Late delivery'
        WHEN is_late_delivery IS FALSE
            THEN 'On-time delivery'
        ELSE 'Not eligible for delivery comparison'
    END AS delivery_performance_group,

    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE scored_review_records > 0
    ) AS orders_with_reviews,

    SUM(review_records) AS total_review_records,

    SUM(scored_review_records) AS scored_review_records,

    ROUND(
        AVG(average_review_score)
            FILTER (WHERE average_review_score IS NOT NULL),
        2
    ) AS average_review_score,

    COUNT(*) FILTER (
        WHERE average_review_score <= 2
    ) AS orders_with_negative_average_review,

    COUNT(*) FILTER (
        WHERE average_review_score >= 4
    ) AS orders_with_positive_average_review,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE average_review_score <= 2
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE average_review_score IS NOT NULL
            ),
            0
        ),
        2
    ) AS negative_review_order_percentage,

    ROUND(
        AVG(delivery_days)::numeric,
        2
    ) AS average_delivery_days,

    ROUND(
        AVG(delivery_variance_days)::numeric,
        2
    ) AS average_delivery_variance_days,

    ROUND(
        AVG(expected_order_value)::numeric,
        2
    ) AS average_expected_order_value

FROM analytics.vw_order_review_performance

GROUP BY
    CASE
        WHEN is_late_delivery IS TRUE
            THEN 'Late delivery'
        WHEN is_late_delivery IS FALSE
            THEN 'On-time delivery'
        ELSE 'Not eligible for delivery comparison'
    END;


-- ------------------------------------------------------------
-- VIEW 3: Product category and customer satisfaction
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_category_review_analysis AS

WITH order_category AS (

    SELECT
        foi.order_id,

        COALESCE(
            NULLIF(
                BTRIM(dp.product_category_name_english),
                ''
            ),
            NULLIF(
                BTRIM(dp.product_category_name),
                ''
            ),
            'uncategorized'
        ) AS product_category,

        COUNT(*) AS item_lines,

        COUNT(DISTINCT foi.product_key) AS distinct_products,

        COUNT(DISTINCT foi.seller_key) AS distinct_sellers,

        SUM(foi.price) AS product_value,

        SUM(foi.freight_value) AS freight_value

    FROM analytics.fact_order_items foi

    INNER JOIN analytics.dim_products dp
        ON foi.product_key = dp.product_key

    GROUP BY
        foi.order_id,
        COALESCE(
            NULLIF(
                BTRIM(dp.product_category_name_english),
                ''
            ),
            NULLIF(
                BTRIM(dp.product_category_name),
                ''
            ),
            'uncategorized'
        )
),

category_product_count AS (

    SELECT
        COALESCE(
            NULLIF(BTRIM(dp.product_category_name_english), ''),
            NULLIF(BTRIM(dp.product_category_name), ''),
            'uncategorized'
        ) AS product_category,

        COUNT(DISTINCT foi.product_key) AS actual_product_count

    FROM analytics.fact_order_items foi

    INNER JOIN analytics.dim_products dp
        ON foi.product_key = dp.product_key

    GROUP BY 1
)

SELECT
    oc.product_category,

    COUNT(DISTINCT oc.order_id) AS total_orders,

    SUM(oc.item_lines) AS total_item_lines,

    cpc.actual_product_count
        AS product_count_across_order_categories,

    SUM(oc.product_value) AS total_product_value,

    SUM(oc.freight_value) AS total_freight_value,

    COUNT(DISTINCT orp.order_id) FILTER (
        WHERE orp.order_status = 'delivered'
    ) AS delivered_orders,

    COUNT(DISTINCT orp.order_id) FILTER (
        WHERE orp.is_late_delivery IS TRUE
    ) AS late_delivery_orders,

    ROUND(
        100.0 * COUNT(DISTINCT orp.order_id) FILTER (
            WHERE orp.is_late_delivery IS TRUE
        )
        / NULLIF(
            COUNT(DISTINCT orp.order_id) FILTER (
                WHERE orp.is_late_delivery IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_percentage,

    COUNT(DISTINCT orp.order_id) FILTER (
        WHERE orp.average_review_score IS NOT NULL
    ) AS orders_with_reviews,

    ROUND(
        AVG(orp.average_review_score)
            FILTER (
                WHERE orp.average_review_score IS NOT NULL
            ),
        2
    ) AS average_review_score,

    COUNT(DISTINCT orp.order_id) FILTER (
        WHERE orp.average_review_score <= 2
    ) AS negatively_reviewed_orders,

    ROUND(
        100.0 * COUNT(DISTINCT orp.order_id) FILTER (
            WHERE orp.average_review_score <= 2
        )
        / NULLIF(
            COUNT(DISTINCT orp.order_id) FILTER (
                WHERE orp.average_review_score IS NOT NULL
            ),
            0
        ),
        2
    ) AS negative_review_order_percentage

FROM order_category oc

INNER JOIN analytics.vw_order_review_performance orp
    ON oc.order_id = orp.order_id

INNER JOIN category_product_count cpc
    ON oc.product_category = cpc.product_category

GROUP BY
    oc.product_category,
    cpc.actual_product_count;


-- ------------------------------------------------------------
-- VIEW 4: Payment behaviour and delivery performance
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_payment_delivery_analysis AS

SELECT
    COALESCE(
        NULLIF(BTRIM(payment_type), ''),
        'unknown'
    ) AS payment_type,

    CASE
        WHEN payment_installments IS NULL
            THEN 'Unknown'
        WHEN payment_installments = 1
            THEN '1 installment'
        WHEN payment_installments BETWEEN 2 AND 3
            THEN '2-3 installments'
        WHEN payment_installments BETWEEN 4 AND 6
            THEN '4-6 installments'
        WHEN payment_installments BETWEEN 7 AND 12
            THEN '7-12 installments'
        WHEN payment_installments > 12
            THEN 'More than 12 installments'
        ELSE 'Invalid installment count'
    END AS installment_group,

    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
    ) AS delivered_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'canceled'
    ) AS canceled_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
    ) AS delivery_eligible_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date
              > order_estimated_delivery_date
    ) AS late_delivery_orders,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date
                  > order_estimated_delivery_date
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE order_status = 'delivered'
                  AND order_delivered_customer_date IS NOT NULL
                  AND order_estimated_delivery_date IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_percentage,

    ROUND(
        SUM(payment_value),
        2
    ) AS total_payment_value,

    ROUND(
        AVG(payment_value),
        2
    ) AS average_payment_value,

    ROUND(
        AVG(payment_difference),
        2
    ) AS average_payment_difference,

    COUNT(*) FILTER (
        WHERE payment_difference IS NOT NULL
          AND ABS(payment_difference) > 0.01
    ) AS orders_with_payment_discrepancy,

    ROUND(
        AVG(
            EXTRACT(
                EPOCH FROM (
                    order_delivered_customer_date
                    - order_purchase_timestamp
                )
            ) / 86400.0
        )::numeric,
        2
    ) AS average_delivery_days

FROM analytics.vw_order_performance

GROUP BY
    COALESCE(
        NULLIF(BTRIM(payment_type), ''),
        'unknown'
    ),

    CASE
        WHEN payment_installments IS NULL
            THEN 'Unknown'
        WHEN payment_installments = 1
            THEN '1 installment'
        WHEN payment_installments BETWEEN 2 AND 3
            THEN '2-3 installments'
        WHEN payment_installments BETWEEN 4 AND 6
            THEN '4-6 installments'
        WHEN payment_installments BETWEEN 7 AND 12
            THEN '7-12 installments'
        WHEN payment_installments > 12
            THEN 'More than 12 installments'
        ELSE 'Invalid installment count'
    END;


-- ------------------------------------------------------------
-- VIEW 5: Customer segments and product category performance
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_customer_segment_category_analysis AS

WITH customer_category AS (

    SELECT
        dc.customer_unique_id,

        rfm.customer_segment,

        COALESCE(
            NULLIF(
                BTRIM(dp.product_category_name_english),
                ''
            ),
            NULLIF(
                BTRIM(dp.product_category_name),
                ''
            ),
            'uncategorized'
        ) AS product_category,

        foi.order_id,

        foi.price,

        foi.freight_value,

        fo.order_status

    FROM analytics.fact_order_items foi

    INNER JOIN analytics.fact_orders fo
        ON foi.order_id = fo.order_id

    INNER JOIN analytics.dim_customers dc
        ON fo.customer_key = dc.customer_key

    LEFT JOIN analytics.vw_customer_rfm rfm
        ON dc.customer_unique_id = rfm.customer_unique_id

    INNER JOIN analytics.dim_products dp
        ON foi.product_key = dp.product_key
)

SELECT
    COALESCE(
        customer_segment,
        'Unclassified'
    ) AS customer_segment,

    product_category,

    COUNT(DISTINCT customer_unique_id)
        AS distinct_customers,

    COUNT(DISTINCT order_id)
        AS distinct_orders,

    COUNT(*) AS item_lines,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
    ) AS delivered_item_lines,

    SUM(price) AS total_product_value,

    SUM(price) FILTER (
        WHERE order_status = 'delivered'
    ) AS delivered_product_value,

    SUM(freight_value) AS total_freight_value,

    ROUND(
        SUM(price) FILTER (
            WHERE order_status = 'delivered'
        )
        / NULLIF(
            COUNT(DISTINCT order_id) FILTER (
                WHERE order_status = 'delivered'
            ),
            0
        ),
        2
    ) AS delivered_value_per_order

FROM customer_category

GROUP BY
    COALESCE(
        customer_segment,
        'Unclassified'
    ),
    product_category;
