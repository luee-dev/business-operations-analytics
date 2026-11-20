import pandas as pd


def analyze_seller_performance(
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyse seller revenue contribution, productivity,
    fulfilment and delivery performance.

    Undefined metrics remain NaN when their denominator is zero.
    """
    required_columns = {
        "seller_id",
        "seller_city",
        "seller_state",
        "delivery_estimate_eligible_orders",
        "late_delivery_order_associations",
        "delivered_product_value",
    }

    missing_columns = required_columns.difference(sellers.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    if sellers["seller_id"].duplicated().any():
        raise ValueError("Expected one row per seller.")

    # These fields should always be present.
    non_nullable_columns = [
        "seller_id",
        "seller_city",
        "seller_state",
        "total_order_associations",
        "delivered_order_associations",
        "canceled_order_associations",
        "distinct_customers",
        "distinct_products_sold",
        "delivered_product_value",
        "delivered_item_lines",
        "shipping_deadline_eligible_item_lines",
        "delivered_order_percentage",
        "canceled_order_percentage",
    ]

    if sellers[non_nullable_columns].isna().any().any():
        raise ValueError("Unexpected missing values in required seller fields.")

    # Missing delivery metrics are only valid when there are
    # no delivered associations.
    delivery_metrics = [
        "average_delivered_order_value",
        "avg_purchase_to_carrier_days",
        "avg_carrier_to_customer_days",
        "avg_total_delivery_days",
        "median_total_delivery_days",
        "p90_total_delivery_days",
        "late_delivery_percentage",
        "on_time_delivery_percentage",
        "delivered_value_per_order_association",
    ]

    zero_delivery = sellers["delivered_order_associations"] == 0

    if sellers.loc[~zero_delivery, delivery_metrics].isna().any().any():
        raise ValueError(
            "Unexpected missing delivery metrics for sellers "
            "with delivered associations."
        )

    # A missing shipping-deadline rate is valid only when
    # the eligible item-line denominator is zero.
    zero_shipping_eligible = sellers["shipping_deadline_eligible_item_lines"] == 0

    if (
        sellers.loc[
            ~zero_shipping_eligible,
            "shipping_deadline_late_percentage",
        ]
        .isna()
        .any()
    ):
        raise ValueError("Missing shipping-deadline rate despite eligible item lines.")

    result = sellers.copy()

    total_revenue = result["delivered_product_value"].sum()

    if total_revenue <= 0:
        raise ValueError("Total delivered revenue must be positive.")

    result["revenue_share"] = result["delivered_product_value"] / total_revenue * 100

    result["revenue_per_product"] = result["delivered_product_value"] / result[
        "distinct_products_sold"
    ].replace(0, pd.NA)

    result["revenue_per_customer"] = result["delivered_product_value"] / result[
        "distinct_customers"
    ].replace(0, pd.NA)

    result["items_per_delivered_association"] = result["delivered_item_lines"] / result[
        "delivered_order_associations"
    ].replace(0, pd.NA)

    result = result.sort_values(
        "delivered_product_value",
        ascending=False,
    ).reset_index(drop=True)

    result["revenue_rank"] = range(1, len(result) + 1)

    result["cumulative_revenue_share"] = result["revenue_share"].cumsum()

    return result


def summarize_seller_concentration(
    sellers: pd.DataFrame,
) -> dict:
    """
    Summarise seller revenue concentration and coverage.
    """
    required_columns = {
        "seller_id",
        "delivered_product_value",
    }

    missing_columns = required_columns.difference(sellers.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    if sellers["seller_id"].duplicated().any():
        raise ValueError("Expected one row per seller.")

    if sellers["delivered_product_value"].isna().any():
        raise ValueError("Delivered revenue contains missing values.")

    if (sellers["delivered_product_value"] < 0).any():
        raise ValueError("Delivered revenue contains negative values.")

    total_revenue = sellers["delivered_product_value"].sum()

    if total_revenue <= 0:
        raise ValueError("Total delivered revenue must be positive.")

    selling_sellers = sellers.loc[sellers["delivered_product_value"] > 0].copy()

    shares = selling_sellers["delivered_product_value"] / total_revenue * 100

    ranked = selling_sellers.sort_values(
        "delivered_product_value",
        ascending=False,
    )

    return {
        "total_sellers": len(sellers),
        "sellers_with_delivered_sales": len(selling_sellers),
        "sellers_without_delivered_sales": (len(sellers) - len(selling_sellers)),
        "top_10_revenue_share": shares.nlargest(10).sum(),
        "top_20_revenue_share": shares.nlargest(20).sum(),
        "top_50_revenue_share": shares.nlargest(50).sum(),
        "seller_revenue_hhi": (shares**2).sum(),
        "total_delivered_product_value": total_revenue,
        "top_10_seller_ids": ranked.head(10)["seller_id"].tolist(),
    }


def analyze_seller_operational_risk(
    sellers: pd.DataFrame,
    minimum_eligible: int = 30,
) -> pd.DataFrame:
    """
    Identify sellers with statistically elevated late-delivery rates.

    Sellers are compared against the weighted late-delivery rate
    among sellers meeting the minimum eligible-association threshold.

    Uses the Wilson 95% lower confidence bound to avoid overreacting
    to high percentages from small samples.
    """
    required_columns = {
        "seller_id",
        "seller_city",
        "seller_state",
        "delivery_estimate_eligible_orders",
        "late_delivery_order_associations",
        "delivered_product_value",
    }

    missing = required_columns.difference(sellers.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    eligible = sellers.loc[
        sellers["delivery_estimate_eligible_orders"] >= minimum_eligible
    ].copy()

    total_revenue = sellers["delivered_product_value"].sum()

    if total_revenue <= 0:
        raise ValueError("Total delivered revenue must be positive.")

    eligible["revenue_share"] = (
        eligible["delivered_product_value"] / total_revenue * 100
    )

    if eligible.empty:
        raise ValueError("No sellers meet the minimum eligibility threshold.")

    n = eligible["delivery_estimate_eligible_orders"]
    late = eligible["late_delivery_order_associations"]

    if (late > n).any() or (late < 0).any():
        raise ValueError("Invalid late-delivery association counts.")

    total_eligible = n.sum()
    total_late = late.sum()

    benchmark = total_late / total_eligible

    eligible["late_delivery_rate"] = late / n
    eligible["benchmark_rate"] = benchmark
    eligible["expected_late_associations"] = n * benchmark
    eligible["excess_late_associations"] = late - eligible["expected_late_associations"]

    # Wilson score interval, using z = 1.96 for 95% confidence.
    z = 1.96
    p = eligible["late_delivery_rate"]
    z_squared = z**2

    denominator = 1 + z_squared / n

    center = (p + z_squared / (2 * n)) / denominator

    margin = z * (p * (1 - p) / n + z_squared / (4 * n**2)) ** 0.5 / denominator

    eligible["late_rate_lower_95"] = center - margin
    eligible["late_rate_upper_95"] = center + margin

    eligible["operational_risk"] = (eligible["late_rate_lower_95"] > benchmark).map(
        {
            True: "Elevated",
            False: "Not statistically elevated",
        }
    )

    return eligible.sort_values(
        ["excess_late_associations", "late_delivery_rate"],
        ascending=False,
    ).reset_index(drop=True)
