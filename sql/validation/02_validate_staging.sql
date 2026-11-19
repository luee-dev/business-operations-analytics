SELECT 'customers' AS dataset, COUNT(*) AS row_count FROM staging.customers
UNION ALL
SELECT 'geolocation', COUNT(*) FROM staging.geolocation
UNION ALL
SELECT 'order_items', COUNT(*) FROM staging.order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM staging.payments
UNION ALL
SELECT 'reviews', COUNT(*) FROM staging.reviews
UNION ALL
SELECT 'orders', COUNT(*) FROM staging.orders
UNION ALL
SELECT 'products', COUNT(*) FROM staging.products
UNION ALL
SELECT 'sellers', COUNT(*) FROM staging.sellers
UNION ALL
SELECT 'category_translation', COUNT(*) FROM staging.category_translation
ORDER BY dataset;


SELECT 'orders_without_customers' AS check_name, COUNT(*) AS issue_count
FROM staging.orders o
LEFT JOIN staging.customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL

SELECT 'order_items_without_orders', COUNT(*)
FROM staging.order_items oi
LEFT JOIN staging.orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT 'order_items_without_products', COUNT(*)
FROM staging.order_items oi
LEFT JOIN staging.products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT 'order_items_without_sellers', COUNT(*)
FROM staging.order_items oi
LEFT JOIN staging.sellers s
    ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL

UNION ALL

SELECT 'payments_without_orders', COUNT(*)
FROM staging.payments p
LEFT JOIN staging.orders o
    ON p.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT 'reviews_without_orders', COUNT(*)
FROM staging.reviews r
LEFT JOIN staging.orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- Duplicate order-item combinations
SELECT order_id, order_item_id, COUNT(*)
FROM staging.order_items
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;

-- Duplicate payment sequences within an order
SELECT order_id, payment_sequential, COUNT(*)
FROM staging.payments
GROUP BY order_id, payment_sequential
HAVING COUNT(*) > 1;

-- Repeated review IDs (expected in this dataset)
SELECT
    COUNT(*) AS repeated_review_ids
FROM (
    SELECT review_id
    FROM staging.reviews
    GROUP BY review_id
    HAVING COUNT(*) > 1
) duplicates;



SELECT
    COUNT(*) FILTER (
        WHERE flag_approval_after_carrier
    ) AS approval_after_carrier,

    COUNT(*) FILTER (
        WHERE flag_carrier_after_customer_delivery
    ) AS carrier_after_customer,

    COUNT(*) FILTER (
        WHERE flag_delivered_missing_timestamp
    ) AS delivered_missing_timestamp,

    COUNT(*) FILTER (
        WHERE flag_approval_after_carrier
           OR flag_carrier_after_customer_delivery
           OR flag_delivered_missing_timestamp
    ) AS orders_with_any_anomaly
FROM staging.orders;

SELECT
    'negative_item_price' AS check_name,
    COUNT(*) AS issue_count
FROM staging.order_items
WHERE price < 0

UNION ALL

SELECT
    'negative_freight_value',
    COUNT(*)
FROM staging.order_items
WHERE freight_value < 0

UNION ALL

SELECT
    'negative_payment_value',
    COUNT(*)
FROM staging.payments
WHERE payment_value < 0;