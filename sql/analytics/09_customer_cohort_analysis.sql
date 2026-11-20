
CREATE OR REPLACE VIEW analytics.vw_customer_cohort_retention AS

WITH delivered_orders AS (
    SELECT
        dc.customer_unique_id,
        DATE_TRUNC(
            'month',
            op.order_purchase_timestamp
        )::date AS activity_month
    FROM analytics.vw_order_performance op
    JOIN analytics.dim_customers dc
        ON op.customer_key = dc.customer_key
    WHERE op.order_status = 'delivered'
      AND op.order_purchase_timestamp IS NOT NULL
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        MIN(activity_month) AS cohort_month
    FROM delivered_orders
    GROUP BY customer_unique_id
),

customer_activity AS (
    SELECT DISTINCT
        customer_unique_id,
        activity_month
    FROM delivered_orders
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),

last_activity_month AS (
    SELECT MAX(activity_month) AS max_month
    FROM customer_activity
),

cohort_month_grid AS (
    SELECT
        cs.cohort_month,
        gs.activity_month::date AS activity_month,
        cs.cohort_size,
        (
            (
                EXTRACT(YEAR FROM gs.activity_month) -
                EXTRACT(YEAR FROM cs.cohort_month)
            ) * 12
            +
            (
                EXTRACT(MONTH FROM gs.activity_month) -
                EXTRACT(MONTH FROM cs.cohort_month)
            )
        )::integer AS cohort_index
    FROM cohort_sizes cs
    CROSS JOIN last_activity_month lm
    CROSS JOIN LATERAL GENERATE_SERIES(
        cs.cohort_month::timestamp,
        lm.max_month::timestamp,
        INTERVAL '1 month'
    ) AS gs(activity_month)
),

cohort_activity_counts AS (
    SELECT
        cc.cohort_month,
        ca.activity_month,
        COUNT(DISTINCT ca.customer_unique_id) AS active_customers
    FROM customer_activity ca
    JOIN customer_cohorts cc
        ON ca.customer_unique_id = cc.customer_unique_id
    GROUP BY
        cc.cohort_month,
        ca.activity_month
)

SELECT
    cmg.cohort_month,
    cmg.activity_month,
    cmg.cohort_index,
    cmg.cohort_size,
    COALESCE(cac.active_customers, 0) AS active_customers,
    ROUND(
        COALESCE(cac.active_customers, 0)::numeric
        / NULLIF(cmg.cohort_size, 0) * 100,
        2
    ) AS retention_percentage
FROM cohort_month_grid cmg
LEFT JOIN cohort_activity_counts cac
    ON cmg.cohort_month = cac.cohort_month
   AND cmg.activity_month = cac.activity_month;
