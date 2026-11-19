
-- ============================================================
-- 03: VALIDATE MONTHLY PERFORMANCE AGGREGATES
-- Compare monthly totals against the complete order dataset
-- ============================================================

WITH monthly AS (
    SELECT
        DATE_TRUNC(
            'month',
            order_purchase_timestamp
        )::DATE AS purchase_month,

        COUNT(*) AS total_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'canceled'
        ) AS canceled_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'shipped'
        ) AS shipped_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date
                  > order_estimated_delivery_date
        ) AS late_delivered_orders,

        SUM(expected_order_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_order_value,

        SUM(payment_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_payment_value

    FROM analytics.vw_order_performance
    WHERE order_purchase_timestamp IS NOT NULL
    GROUP BY 1
),

monthly_totals AS (
    SELECT
        COUNT(*) AS months_in_dataset,
        SUM(total_orders) AS total_orders,
        SUM(delivered_orders) AS delivered_orders,
        SUM(canceled_orders) AS canceled_orders,
        SUM(shipped_orders) AS shipped_orders,
        SUM(late_delivered_orders) AS late_delivered_orders,
        SUM(delivered_order_value) AS delivered_order_value,
        SUM(delivered_payment_value) AS delivered_payment_value
    FROM monthly
),

overall_totals AS (
    SELECT
        COUNT(*) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
        ) AS total_orders,

        COUNT(*) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'canceled'
        ) AS canceled_orders,

        COUNT(*) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'shipped'
        ) AS shipped_orders,

        COUNT(*) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'delivered'
              AND order_delivered_customer_date
                  > order_estimated_delivery_date
        ) AS late_delivered_orders,

        SUM(expected_order_value) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'delivered'
        ) AS delivered_order_value,

        SUM(payment_value) FILTER (
            WHERE order_purchase_timestamp IS NOT NULL
              AND order_status = 'delivered'
        ) AS delivered_payment_value

    FROM analytics.vw_order_performance
)

SELECT
    m.months_in_dataset,

    m.total_orders AS monthly_total_orders,
    o.total_orders AS overall_total_orders,
    m.total_orders - o.total_orders AS order_difference,

    m.delivered_orders,
    o.delivered_orders AS overall_delivered_orders,
    m.delivered_orders - o.delivered_orders
        AS delivered_difference,

    m.canceled_orders,
    o.canceled_orders AS overall_canceled_orders,
    m.canceled_orders - o.canceled_orders
        AS canceled_difference,

    m.shipped_orders,
    o.shipped_orders AS overall_shipped_orders,
    m.shipped_orders - o.shipped_orders
        AS shipped_difference,

    m.late_delivered_orders,
    o.late_delivered_orders AS overall_late_delivered_orders,
    m.late_delivered_orders - o.late_delivered_orders
        AS late_delivery_difference,

    ROUND(m.delivered_order_value, 2)
        AS monthly_delivered_order_value,

    ROUND(o.delivered_order_value, 2)
        AS overall_delivered_order_value,

    ROUND(
        m.delivered_order_value - o.delivered_order_value,
        2
    ) AS order_value_difference,

    ROUND(m.delivered_payment_value, 2)
        AS monthly_delivered_payment_value,

    ROUND(o.delivered_payment_value, 2)
        AS overall_delivered_payment_value,

    ROUND(
        m.delivered_payment_value - o.delivered_payment_value,
        2
    ) AS payment_value_difference

FROM monthly_totals m
CROSS JOIN overall_totals o;
