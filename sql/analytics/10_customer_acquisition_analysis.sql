
CREATE OR REPLACE VIEW analytics.vw_customer_acquisition AS

WITH delivered_orders AS (
    SELECT
        dc.customer_unique_id,
        op.order_id,
        DATE_TRUNC(
            'month',
            op.order_purchase_timestamp
        )::date AS activity_month,
        op.expected_order_value
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

customer_cohort_summary AS (
    SELECT
        cc.customer_unique_id,
        cc.cohort_month,

        COUNT(dord.order_id) AS lifetime_delivered_orders,
        SUM(dord.expected_order_value) AS lifetime_delivered_value,

        COUNT(dord.order_id) FILTER (
            WHERE dord.activity_month = cc.cohort_month
        ) AS first_month_delivered_orders,

        SUM(dord.expected_order_value) FILTER (
            WHERE dord.activity_month = cc.cohort_month
        ) AS first_month_delivered_value

    FROM customer_cohorts cc
    JOIN delivered_orders dord
        ON cc.customer_unique_id = dord.customer_unique_id
    GROUP BY
        cc.customer_unique_id,
        cc.cohort_month
),

monthly_cohort_summary AS (
    SELECT
        cohort_month,
        COUNT(*) AS new_customers,
        SUM(first_month_delivered_orders) AS first_month_delivered_orders,
        SUM(first_month_delivered_value) AS first_month_delivered_value,
        SUM(lifetime_delivered_orders) AS lifetime_delivered_orders,
        SUM(lifetime_delivered_value) AS lifetime_delivered_value,

        COUNT(*) FILTER (
            WHERE lifetime_delivered_orders > 1
        ) AS repeat_customers

    FROM customer_cohort_summary
    GROUP BY cohort_month
),

calendar_months AS (
    SELECT
        GENERATE_SERIES(
            (SELECT MIN(cohort_month) FROM monthly_cohort_summary),
            (SELECT MAX(cohort_month) FROM monthly_cohort_summary),
            INTERVAL '1 month'
        )::date AS cohort_month
),

monthly_acquisition AS (
    SELECT
        cm.cohort_month,

        COALESCE(ms.new_customers, 0) AS new_customers,
        COALESCE(ms.first_month_delivered_orders, 0)
            AS first_month_delivered_orders,
        COALESCE(ms.first_month_delivered_value, 0)
            AS first_month_delivered_value,
        COALESCE(ms.lifetime_delivered_orders, 0)
            AS lifetime_delivered_orders,
        COALESCE(ms.lifetime_delivered_value, 0)
            AS lifetime_delivered_value,
        COALESCE(ms.repeat_customers, 0) AS repeat_customers

    FROM calendar_months cm
    LEFT JOIN monthly_cohort_summary ms
        ON cm.cohort_month = ms.cohort_month
),

acquisition_with_growth AS (
    SELECT
        *,

        LAG(new_customers) OVER (
            ORDER BY cohort_month
        ) AS previous_month_customers

    FROM monthly_acquisition
)

SELECT
    cohort_month,
    new_customers,
    previous_month_customers,

    CASE
        WHEN previous_month_customers IS NULL
          OR previous_month_customers = 0
        THEN NULL
        ELSE ROUND(
            (
                new_customers - previous_month_customers
            )::numeric
            / previous_month_customers * 100,
            2
        )
    END AS acquisition_growth_percentage,

    first_month_delivered_orders,
    ROUND(first_month_delivered_value, 2)
        AS first_month_delivered_value,

    ROUND(
        first_month_delivered_value
        / NULLIF(new_customers, 0),
        2
    ) AS average_first_month_value_per_customer,

    ROUND(
        first_month_delivered_value
        / NULLIF(first_month_delivered_orders, 0),
        2
    ) AS first_month_average_order_value,

    lifetime_delivered_orders,
    ROUND(lifetime_delivered_value, 2)
        AS lifetime_delivered_value,

    ROUND(
        lifetime_delivered_value
        / NULLIF(new_customers, 0),
        2
    ) AS average_lifetime_customer_value,

    repeat_customers,

    ROUND(
        repeat_customers::numeric
        / NULLIF(new_customers, 0) * 100,
        2
    ) AS cohort_repeat_customer_percentage

FROM acquisition_with_growth;
