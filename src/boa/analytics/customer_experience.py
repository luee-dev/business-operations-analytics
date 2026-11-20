import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import (
    proportion_confint,
    proportions_ztest,
)
from statsmodels.stats.weightstats import ttest_ind

REQUIRED_COLUMNS = {
    "order_id",
    "order_status",
    "is_late_delivery",
    "delivery_days",
    "average_review_score",
    "scored_review_records",
    "negative_review_records",
}


def analyze_customer_experience(orders: pd.DataFrame) -> dict:
    """
    Compare order-level review outcomes for late and on-time deliveries.

    The input must contain one row per order. Only delivered orders with
    valid delivery classification and at least one scored review are used.

    An order is classified as having a negative review if it has at least
    one negative review record. Each order contributes only once to this
    binary comparison.
    """
    missing = REQUIRED_COLUMNS - set(orders.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if orders["order_id"].duplicated().any():
        raise ValueError("Expected one row per order; duplicate order_id found")

    valid_delivery_values = orders["is_late_delivery"].dropna()

    if not valid_delivery_values.isin([True, False]).all():
        raise TypeError("is_late_delivery must contain only boolean values or nulls")

    data = orders.loc[
        (orders["order_status"] == "delivered")
        & orders["is_late_delivery"].notna()
        & orders["average_review_score"].notna()
        & (orders["scored_review_records"] > 0)
    ].copy()

    if data.empty:
        raise ValueError("No eligible delivered orders with scored reviews")

    valid_delivery_values = orders["is_late_delivery"].dropna()

    if not valid_delivery_values.isin([True, False]).all():
        raise TypeError("is_late_delivery must contain only boolean values or nulls")

    if (data["negative_review_records"] < 0).any():
        raise ValueError("negative_review_records cannot be negative")

    data["has_negative_review"] = data["negative_review_records"] > 0

    late = data.loc[data["is_late_delivery"].eq(True)].copy()
    on_time = data.loc[data["is_late_delivery"].eq(False)].copy()

    if late.empty or on_time.empty:
        raise ValueError("Both late and on-time groups must contain observations")

    def summarize(group: pd.DataFrame) -> dict:
        negative_orders = int(group["has_negative_review"].sum())
        order_count = len(group)

        ci_low, ci_high = proportion_confint(
            count=negative_orders,
            nobs=order_count,
            alpha=0.05,
            method="wilson",
        )

        scored_reviews = int(group["scored_review_records"].sum())
        negative_reviews = int(group["negative_review_records"].sum())

        return {
            "orders": order_count,
            "average_review_score": float(group["average_review_score"].mean()),
            "median_review_score": float(group["average_review_score"].median()),
            "negative_review_orders": negative_orders,
            "negative_review_order_rate": negative_orders / order_count,
            "negative_review_order_rate_ci_95": (float(ci_low), float(ci_high)),
            "scored_review_records": scored_reviews,
            "negative_review_records": negative_reviews,
            "negative_review_record_rate": (
                negative_reviews / scored_reviews if scored_reviews else float("nan")
            ),
            "average_delivery_days": float(group["delivery_days"].mean()),
        }

    late_summary = summarize(late)
    on_time_summary = summarize(on_time)

    # Welch's t-test compares order-level average review scores.
    t_stat, score_p_value, degrees_freedom = ttest_ind(
        late["average_review_score"].to_numpy(),
        on_time["average_review_score"].to_numpy(),
        usevar="unequal",
        alternative="two-sided",
    )

    # Non-parametric comparison of order-level review-score distributions.
    mann_whitney = mannwhitneyu(
        late["average_review_score"].to_numpy(),
        on_time["average_review_score"].to_numpy(),
        alternative="two-sided",
        method="asymptotic",
    )

    # Two-proportion z-test compares the share of orders with at least
    # one negative review. Each order contributes one binary observation.
    negative_counts = [
        late_summary["negative_review_orders"],
        on_time_summary["negative_review_orders"],
    ]
    group_sizes = [
        late_summary["orders"],
        on_time_summary["orders"],
    ]

    z_stat, negative_rate_p_value = proportions_ztest(
        count=negative_counts,
        nobs=group_sizes,
        alternative="two-sided",
    )

    return {
        "eligible_orders": len(data),
        "late": late_summary,
        "on_time": on_time_summary,
        "differences": {
            "average_review_score": (
                late_summary["average_review_score"]
                - on_time_summary["average_review_score"]
            ),
            "negative_review_order_rate": (
                late_summary["negative_review_order_rate"]
                - on_time_summary["negative_review_order_rate"]
            ),
        },
        "statistical_tests": {
            "welch_t_test_review_score": {
                "statistic": float(t_stat),
                "degrees_freedom": float(degrees_freedom),
                "p_value": float(score_p_value),
            },
            "two_proportion_z_test_negative_review_orders": {
                "statistic": float(z_stat),
                "p_value": float(negative_rate_p_value),
            },
            "mann_whitney_u_review_score": {
                "statistic": float(mann_whitney.statistic),
                "p_value": float(mann_whitney.pvalue),
            },
        },
    }
