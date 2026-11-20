
-- ============================================================
-- LOAD FACT TABLE
-- 04: REVIEWS
-- Grain: One row per staging review record
-- ============================================================

INSERT INTO analytics.fact_reviews (
    staging_review_id,
    review_id,
    order_id,
    review_date_key,
    answer_date_key,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp
)

SELECT
    r.staging_review_id,
    r.review_id,
    r.order_id,

    review_date.date_key,
    answer_date.date_key,

    r.review_score,
    r.review_comment_title,
    r.review_comment_message,
    r.review_creation_date,
    r.review_answer_timestamp

FROM staging.reviews r

INNER JOIN analytics.fact_orders o
    ON r.order_id = o.order_id

LEFT JOIN analytics.dim_date review_date
    ON r.review_creation_date::DATE = review_date.calendar_date

LEFT JOIN analytics.dim_date answer_date
    ON r.review_answer_timestamp::DATE = answer_date.calendar_date

ON CONFLICT (staging_review_id)
DO UPDATE SET
    review_id = EXCLUDED.review_id,
    order_id = EXCLUDED.order_id,
    review_date_key = EXCLUDED.review_date_key,
    answer_date_key = EXCLUDED.answer_date_key,
    review_score = EXCLUDED.review_score,
    review_comment_title = EXCLUDED.review_comment_title,
    review_comment_message = EXCLUDED.review_comment_message,
    review_creation_date = EXCLUDED.review_creation_date,
    review_answer_timestamp = EXCLUDED.review_answer_timestamp;


-- ============================================================
-- VALIDATE FACT REVIEWS
-- ============================================================

SELECT
    COUNT(*) AS total_reviews,

    COUNT(DISTINCT staging_review_id)
        AS unique_review_records,

    COUNT(DISTINCT review_id)
        AS distinct_review_ids,

    COUNT(DISTINCT order_id)
        AS orders_with_reviews,

    ROUND(AVG(review_score), 2)
        AS average_review_score,

    COUNT(*) FILTER (
        WHERE review_score IS NULL
    ) AS missing_review_scores,

    COUNT(*) FILTER (
        WHERE review_creation_date IS NULL
    ) AS missing_review_dates,

    COUNT(*) FILTER (
        WHERE review_answer_timestamp IS NULL
    ) AS missing_answer_timestamps,

    COUNT(*) FILTER (
        WHERE review_comment_message IS NULL
    ) AS missing_review_comments

FROM analytics.fact_reviews;
