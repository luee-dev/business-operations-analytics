
-- ============================================================
-- 08_customer_analysis.sql
-- Customer Purchasing Behaviour and Segmentation
-- Dataset: Olist Brazilian E-Commerce
-- ============================================================

-- ------------------------------------------------------------
-- 1. CUSTOMER PERFORMANCE VIEW
-- One row per actual customer (customer_unique_id).
-- Monetary metrics are calculated from delivered orders only.
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_customer_performance AS

WITH customer_orders AS (
    SELECT
        dc.customer_unique_id,
        dc.customer_key,
        dc.customer_id,

        op.order_id,
        op.order_status,
        op.order_purchase_timestamp,
        op.expected_order_value,
        op.payment_value,
        op.order_delivered_customer_date

    FROM analytics.vw_order_performance op
    JOIN analytics.dim_customers dc
        ON op.customer_key = dc.customer_key
),

customer_aggregates AS (
    SELECT
        customer_unique_id,

        COUNT(DISTINCT customer_id) AS customer_id_count,

        COUNT(DISTINCT order_id) AS total_orders,

        COUNT(DISTINCT order_id)
            FILTER (WHERE order_status = 'delivered')
            AS delivered_orders,

        COUNT(DISTINCT order_id)
            FILTER (WHERE order_status = 'canceled')
            AS canceled_orders,

        COUNT(DISTINCT order_id)
            FILTER (WHERE order_status <> 'delivered')
            AS non_delivered_orders,

        MIN(order_purchase_timestamp) AS first_purchase_date,

        MAX(order_purchase_timestamp) AS last_purchase_date,

        MAX(order_purchase_timestamp)
            FILTER (WHERE order_status = 'delivered')
            AS last_delivered_purchase_date,

        SUM(expected_order_value)
            FILTER (WHERE order_status = 'delivered')
            AS delivered_order_value,

        SUM(payment_value)
            FILTER (WHERE order_status = 'delivered')
            AS delivered_payment_value,

        AVG(expected_order_value)
            FILTER (WHERE order_status = 'delivered')
            AS average_delivered_order_value

    FROM customer_orders
    GROUP BY customer_unique_id
)

SELECT
    customer_unique_id,
    customer_id_count,
    total_orders,
    delivered_orders,
    canceled_orders,
    non_delivered_orders,

    first_purchase_date,
    last_purchase_date,
    last_delivered_purchase_date,

    delivered_order_value,
    delivered_payment_value,
    average_delivered_order_value,

    CASE
        WHEN delivered_orders > 1 THEN 'Repeat Customer'
        WHEN delivered_orders = 1 THEN 'One-time Customer'
        ELSE 'No Delivered Orders'
    END AS customer_type

FROM customer_aggregates;


-- ------------------------------------------------------------
-- 2. CUSTOMER POPULATION AND REPEAT PURCHASE SUMMARY
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_customers,

    COUNT(*) FILTER (
        WHERE delivered_orders > 0
    ) AS customers_with_delivered_orders,

    COUNT(*) FILTER (
        WHERE delivered_orders = 1
    ) AS one_time_customers,

    COUNT(*) FILTER (
        WHERE delivered_orders > 1
    ) AS repeat_customers,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE delivered_orders > 1
        ) / NULLIF(
            COUNT(*) FILTER (WHERE delivered_orders > 0), 0
        ),
        2
    ) AS repeat_customer_percentage,

    SUM(delivered_orders) AS total_delivered_orders,

    ROUND(
        SUM(delivered_order_value),
        2
    ) AS total_delivered_order_value,

    ROUND(
        AVG(average_delivered_order_value),
        2
    ) AS average_customer_order_value

FROM analytics.vw_customer_performance;


-- ------------------------------------------------------------
-- 3. DISTRIBUTION OF CUSTOMERS BY PURCHASE FREQUENCY
-- ------------------------------------------------------------

SELECT
    CASE
        WHEN delivered_orders = 0 THEN '0 delivered orders'
        WHEN delivered_orders = 1 THEN '1 delivered order'
        WHEN delivered_orders BETWEEN 2 AND 3 THEN '2-3 delivered orders'
        WHEN delivered_orders BETWEEN 4 AND 5 THEN '4-5 delivered orders'
        ELSE '6+ delivered orders'
    END AS purchase_frequency_group,

    COUNT(*) AS customer_count,

    ROUND(
        100.0 * COUNT(*) /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS percentage_of_customers,

    ROUND(
        SUM(delivered_order_value),
        2
    ) AS delivered_order_value

FROM analytics.vw_customer_performance

GROUP BY 1
ORDER BY
    MIN(delivered_orders);


-- ------------------------------------------------------------
-- 4. CUSTOMER VALUE SUMMARY
-- Compare one-time and repeat customers.
-- ------------------------------------------------------------

SELECT
    customer_type,

    COUNT(*) AS customer_count,

    SUM(delivered_orders) AS delivered_orders,

    ROUND(
        AVG(delivered_orders),
        2
    ) AS average_delivered_orders_per_customer,

    ROUND(
        AVG(delivered_order_value),
        2
    ) AS average_customer_value,

    ROUND(
        SUM(delivered_order_value),
        2
    ) AS total_customer_value,

    ROUND(
        AVG(average_delivered_order_value),
        2
    ) AS average_order_value

FROM analytics.vw_customer_performance

WHERE delivered_orders > 0

GROUP BY customer_type
ORDER BY total_customer_value DESC;


-- ------------------------------------------------------------
-- 5. TOP 20 CUSTOMERS BY DELIVERED ORDER VALUE
-- ------------------------------------------------------------

SELECT
    customer_unique_id,
    delivered_orders,

    ROUND(delivered_order_value, 2) AS delivered_order_value,

    ROUND(
        average_delivered_order_value,
        2
    ) AS average_order_value,

    last_delivered_purchase_date

FROM analytics.vw_customer_performance

WHERE delivered_orders > 0

ORDER BY delivered_order_value DESC

LIMIT 20;




-- ------------------------------------------------------------
-- 6. CUSTOMER PURCHASE RECENCY
-- Reference date is the latest delivered purchase in dataset.
-- ------------------------------------------------------------

WITH reference_date AS (
    SELECT
        MAX(last_delivered_purchase_date)::date AS max_date
    FROM analytics.vw_customer_performance
),

customer_recency AS (
    SELECT
        cp.customer_unique_id,
        cp.delivered_orders,
        cp.delivered_order_value,

        (
            rd.max_date -
            cp.last_delivered_purchase_date::date
        ) AS recency_days

    FROM analytics.vw_customer_performance cp
    CROSS JOIN reference_date rd

    WHERE cp.delivered_orders > 0
),

recency_segments AS (
    SELECT
        customer_unique_id,
        delivered_orders,
        delivered_order_value,
        recency_days,

        CASE
            WHEN recency_days <= 30 THEN '0-30 days'
            WHEN recency_days <= 90 THEN '31-90 days'
            WHEN recency_days <= 180 THEN '91-180 days'
            WHEN recency_days <= 365 THEN '181-365 days'
            ELSE 'Over 365 days'
        END AS recency_group,

        CASE
            WHEN recency_days <= 30 THEN 1
            WHEN recency_days <= 90 THEN 2
            WHEN recency_days <= 180 THEN 3
            WHEN recency_days <= 365 THEN 4
            ELSE 5
        END AS recency_sort_order

    FROM customer_recency
)

SELECT
    recency_group,

    COUNT(*) AS customer_count,

    ROUND(
        100.0 * COUNT(*) /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS percentage_of_customers,

    ROUND(
        SUM(delivered_order_value),
        2
    ) AS delivered_order_value

FROM recency_segments

GROUP BY
    recency_group,
    recency_sort_order

ORDER BY recency_sort_order;





-- ------------------------------------------------------------
-- 7. RFM CUSTOMER SEGMENTATION - REVISED SCORING
--
-- Recency:
--   Percentile ranking; more recent = higher score.
--
-- Frequency:
--   Explicit purchase-frequency thresholds.
--
-- Monetary:
--   Percentile ranking; higher value = higher score.
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW analytics.vw_customer_rfm AS

WITH reference_date AS (
    SELECT
        MAX(last_delivered_purchase_date)::date AS max_date
    FROM analytics.vw_customer_performance
),

customer_metrics AS (
    SELECT
        cp.customer_unique_id,
        cp.delivered_orders AS frequency,
        cp.delivered_order_value AS monetary,

        (
            rd.max_date -
            cp.last_delivered_purchase_date::date
        ) AS recency_days

    FROM analytics.vw_customer_performance cp
    CROSS JOIN reference_date rd

    WHERE cp.delivered_orders > 0
),

ranked_customers AS (
    SELECT
        *,

        PERCENT_RANK() OVER (
            ORDER BY recency_days DESC
        ) AS recency_percentile,

        PERCENT_RANK() OVER (
            ORDER BY monetary ASC
        ) AS monetary_percentile

    FROM customer_metrics
),

rfm_scores AS (
    SELECT
        *,

        LEAST(
            5,
            FLOOR(recency_percentile * 5)::integer + 1
        ) AS recency_score,

        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency BETWEEN 4 AND 5 THEN 4
            ELSE 5
        END AS frequency_score,

        LEAST(
            5,
            FLOOR(monetary_percentile * 5)::integer + 1
        ) AS monetary_score

    FROM ranked_customers
),

classified_customers AS (
    SELECT
        *,

        CASE
            WHEN recency_score >= 4
             AND frequency_score >= 2
             AND monetary_score >= 4
                THEN 'Champions'

            WHEN recency_score >= 3
             AND frequency_score >= 2
                THEN 'Loyal Customers'

            WHEN recency_score <= 2
             AND frequency_score >= 2
                THEN 'At Risk'

            WHEN recency_score <= 2
             AND frequency_score = 1
                THEN 'Inactive / Hibernating'

            WHEN recency_score >= 4
             AND monetary_score = 5
                THEN 'Recent High-Value Customers'

            WHEN recency_score >= 3
             AND monetary_score >= 4
                THEN 'Potential High Value'

            ELSE 'Regular Customers'
        END AS customer_segment

    FROM rfm_scores
)


SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,

    recency_score,
    frequency_score,
    monetary_score,

    (
        recency_score::text ||
        frequency_score::text ||
        monetary_score::text
    ) AS rfm_score,

    customer_segment

FROM classified_customers;


-- ------------------------------------------------------------
-- 8. RFM SEGMENT SUMMARY
-- ------------------------------------------------------------

SELECT
    customer_segment,

    COUNT(*) AS customer_count,

    ROUND(
        100.0 * COUNT(*) /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS customer_percentage,

    SUM(frequency) AS delivered_orders,

    ROUND(
        SUM(monetary),
        2
    ) AS delivered_order_value,

    ROUND(
        AVG(monetary),
        2
    ) AS average_customer_value,

    ROUND(
        AVG(recency_days),
        1
    ) AS average_recency_days

FROM analytics.vw_customer_rfm

GROUP BY customer_segment

ORDER BY delivered_order_value DESC;


-- ------------------------------------------------------------
-- 9. RFM SCORE DISTRIBUTION
-- ------------------------------------------------------------

SELECT
    rfm_score,
    COUNT(*) AS customer_count,

    ROUND(
        100.0 * COUNT(*) /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS customer_percentage

FROM analytics.vw_customer_rfm

GROUP BY rfm_score

ORDER BY rfm_score DESC;


-- ------------------------------------------------------------
-- 10. TOP 20 CUSTOMERS BY RFM MONETARY VALUE
-- ------------------------------------------------------------

SELECT
    customer_unique_id,
    rfm_score,
    customer_segment,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary_value

FROM analytics.vw_customer_rfm

ORDER BY
    monetary DESC,
    frequency DESC

LIMIT 20;


-- ------------------------------------------------------------
-- 11. CUSTOMER PURCHASE INTERVALS
-- Measures time between consecutive delivered purchases.
-- Only customers with at least two delivered orders qualify.
-- ------------------------------------------------------------

WITH ordered_purchases AS (
    SELECT
        dc.customer_unique_id,
        op.order_id,
        op.order_purchase_timestamp,

        LAG(op.order_purchase_timestamp) OVER (
            PARTITION BY dc.customer_unique_id
            ORDER BY op.order_purchase_timestamp
        ) AS previous_purchase_date

    FROM analytics.vw_order_performance op

    JOIN analytics.dim_customers dc
        ON op.customer_key = dc.customer_key

    WHERE op.order_status = 'delivered'
),

purchase_intervals AS (
    SELECT
        customer_unique_id,
        order_id,

        EXTRACT(
            EPOCH FROM (
                order_purchase_timestamp -
                previous_purchase_date
            )
        ) / 86400.0 AS days_between_purchases

    FROM ordered_purchases

    WHERE previous_purchase_date IS NOT NULL
),

customer_intervals AS (
    SELECT
        customer_unique_id,

        COUNT(*) AS repeat_purchase_intervals,

        AVG(days_between_purchases) AS average_days_between_purchases,

        MIN(days_between_purchases) AS minimum_days_between_purchases,

        MAX(days_between_purchases) AS maximum_days_between_purchases

    FROM purchase_intervals

    GROUP BY customer_unique_id
)

SELECT
    COUNT(*) AS repeat_customers,

    SUM(repeat_purchase_intervals) AS total_purchase_intervals,

    ROUND(
        AVG(average_days_between_purchases),
        2
    ) AS average_customer_purchase_interval_days,

    ROUND(
        percentile_cont(0.5) WITHIN GROUP (
            ORDER BY average_days_between_purchases
        )::numeric,
        2
    ) AS median_customer_purchase_interval_days,

    ROUND(
        percentile_cont(0.9) WITHIN GROUP (
            ORDER BY average_days_between_purchases
        )::numeric,
        2
    ) AS p90_customer_purchase_interval_days

FROM customer_intervals;


-- ------------------------------------------------------------
-- 12. PURCHASE INTERVAL DISTRIBUTION
-- ------------------------------------------------------------

WITH ordered_purchases AS (
    SELECT
        dc.customer_unique_id,
        op.order_purchase_timestamp,

        LAG(op.order_purchase_timestamp) OVER (
            PARTITION BY dc.customer_unique_id
            ORDER BY op.order_purchase_timestamp
        ) AS previous_purchase_date

    FROM analytics.vw_order_performance op

    JOIN analytics.dim_customers dc
        ON op.customer_key = dc.customer_key

    WHERE op.order_status = 'delivered'
),

purchase_intervals AS (
    SELECT
        EXTRACT(
            EPOCH FROM (
                order_purchase_timestamp -
                previous_purchase_date
            )
        ) / 86400.0 AS days_between_purchases

    FROM ordered_purchases

    WHERE previous_purchase_date IS NOT NULL
)

SELECT
    CASE
        WHEN days_between_purchases <= 30 THEN '0-30 days'
        WHEN days_between_purchases <= 90 THEN '31-90 days'
        WHEN days_between_purchases <= 180 THEN '91-180 days'
        WHEN days_between_purchases <= 365 THEN '181-365 days'
        ELSE 'Over 365 days'
    END AS purchase_interval_group,

    COUNT(*) AS purchase_intervals,

    ROUND(
        AVG(days_between_purchases),
        2
    ) AS average_interval_days

FROM purchase_intervals

GROUP BY 1

ORDER BY
    MIN(days_between_purchases);
