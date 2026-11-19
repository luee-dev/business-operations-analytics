
-- ============================================================
-- 07: MONTHLY ORDER PERFORMANCE ANALYSIS
-- ============================================================

WITH monthly_performance AS (
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

        SUM(product_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_product_value,

        SUM(freight_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_freight_value,

        SUM(expected_order_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_order_value,

        SUM(payment_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_payment_value,

        AVG(expected_order_value) FILTER (
            WHERE order_status = 'delivered'
        ) AS average_delivered_order_value,

        AVG(
            EXTRACT(
                EPOCH FROM (
                    order_delivered_customer_date
                    - order_purchase_timestamp
                )
            ) / 86400.0
        ) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date IS NOT NULL
        ) AS average_delivery_days,

        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date
                  > order_estimated_delivery_date
        ) AS late_delivered_orders

    FROM analytics.vw_order_performance

    WHERE order_purchase_timestamp IS NOT NULL

    GROUP BY 1
)

SELECT
    purchase_month,
    total_orders,
    delivered_orders,
    canceled_orders,
    shipped_orders,

    ROUND(
        100.0 * delivered_orders
        / NULLIF(total_orders, 0),
        2
    ) AS delivered_order_percentage,

    ROUND(
        delivered_product_value,
        2
    ) AS delivered_product_value,

    ROUND(
        delivered_freight_value,
        2
    ) AS delivered_freight_value,

    ROUND(
        delivered_order_value,
        2
    ) AS delivered_order_value,

    ROUND(
        delivered_payment_value,
        2
    ) AS delivered_payment_value,

    ROUND(
        average_delivered_order_value,
        2
    ) AS average_delivered_order_value,

    ROUND(
        average_delivery_days::NUMERIC,
        2
    ) AS average_delivery_days,

    late_delivered_orders,

    ROUND(
        100.0 * late_delivered_orders
        / NULLIF(delivered_orders, 0),
        2
    ) AS late_delivery_percentage

FROM monthly_performance

ORDER BY purchase_month;
