
-- ============================================================
-- LOAD FACT TABLE
-- 03: PAYMENTS
-- Grain: One row per payment sequence per order
-- Natural key: (order_id, payment_sequential)
-- ============================================================

INSERT INTO analytics.fact_payments (
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
)

SELECT
    p.order_id,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value

FROM staging.payments p

INNER JOIN analytics.fact_orders o
    ON p.order_id = o.order_id

ON CONFLICT (order_id, payment_sequential)
DO UPDATE SET
    payment_type = EXCLUDED.payment_type,
    payment_installments = EXCLUDED.payment_installments,
    payment_value = EXCLUDED.payment_value;


-- ============================================================
-- VALIDATE FACT PAYMENTS
-- ============================================================

SELECT
    COUNT(*) AS total_payment_records,

    COUNT(DISTINCT (order_id, payment_sequential))
        AS unique_payment_records,

    COUNT(DISTINCT order_id)
        AS orders_with_payments,

    COUNT(DISTINCT payment_type)
        AS payment_methods,

    SUM(payment_value) AS total_payment_value,

    COUNT(*) FILTER (
        WHERE payment_value = 0
    ) AS zero_value_payments,

    COUNT(*) FILTER (
        WHERE payment_value < 0
    ) AS negative_value_payments,

    COUNT(*) FILTER (
        WHERE payment_installments <= 0
    ) AS invalid_installment_records

FROM analytics.fact_payments;
