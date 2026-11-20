import pandas as pd


def analyze_delivery_performance(orders: pd.DataFrame) -> dict:
    """
    Calculate delivery performance metrics from order-level data.

    Only delivered orders with both actual and estimated delivery
    timestamps are included in the delivery performance denominator.
    """
    required_columns = {
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    }

    missing_columns = required_columns.difference(orders.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    delivered = orders.loc[orders["order_status"].eq("delivered")].copy()

    eligible = delivered.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ).copy()

    eligible["delivery_variance_days"] = (
        eligible["order_delivered_customer_date"]
        - eligible["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    eligible["delivery_days"] = (
        eligible["order_delivered_customer_date"] - eligible["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    late = eligible["delivery_variance_days"] > 0

    late_orders = int(late.sum())
    on_time_orders = int((~late).sum())
    eligible_orders = len(eligible)

    return {
        "total_orders": len(orders),
        "delivered_orders": len(delivered),
        "eligible_orders": eligible_orders,
        "late_orders": late_orders,
        "on_time_orders": on_time_orders,
        "delivered_missing_timestamps": (len(delivered) - eligible_orders),
        "late_delivery_rate": (
            late_orders / eligible_orders * 100 if eligible_orders else 0.0
        ),
        "on_time_delivery_rate": (
            on_time_orders / eligible_orders * 100 if eligible_orders else 0.0
        ),
        "average_delivery_days": eligible["delivery_days"].mean(),
        "median_delivery_days": eligible["delivery_days"].median(),
        "average_delivery_variance_days": (eligible["delivery_variance_days"].mean()),
        "p90_delivery_days": eligible["delivery_days"].quantile(0.90),
    }


def analyze_monthly_delivery_performance(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyze delivery performance by order purchase month.

    Only delivered orders with valid actual and estimated
    delivery timestamps are included.
    """
    required_columns = {
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    }

    missing_columns = required_columns.difference(orders.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    delivered = orders.loc[orders["order_status"].eq("delivered")].copy()

    eligible = delivered.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ).copy()

    eligible["purchase_month"] = eligible["order_purchase_timestamp"].dt.strftime(
        "%Y-%m"
    )

    eligible["delivery_days"] = (
        eligible["order_delivered_customer_date"] - eligible["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    eligible["delivery_variance_days"] = (
        eligible["order_delivered_customer_date"]
        - eligible["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    eligible["is_late"] = eligible["delivery_variance_days"] > 0

    monthly = (
        eligible.groupby("purchase_month", as_index=False)
        .agg(
            eligible_orders=("order_id", "nunique"),
            late_orders=("is_late", "sum"),
            average_delivery_days=("delivery_days", "mean"),
            average_delivery_variance_days=("delivery_variance_days", "mean"),
        )
        .sort_values("purchase_month")
        .reset_index(drop=True)
    )

    # Preserve every calendar month in the observation period.
    purchase_dates = orders["order_purchase_timestamp"].dt.tz_localize(None)
    start_month = purchase_dates.min().to_period("M")
    end_month = purchase_dates.max().to_period("M")

    calendar_months = pd.period_range(
        start=start_month,
        end=end_month,
        freq="M",
    ).astype(str)

    monthly = (
        monthly.set_index("purchase_month")
        .reindex(calendar_months)
        .rename_axis("purchase_month")
        .reset_index()
    )

    count_columns = [
        "eligible_orders",
        "late_orders",
    ]

    monthly[count_columns] = monthly[count_columns].fillna(0).astype(int)

    monthly["on_time_orders"] = monthly["eligible_orders"] - monthly["late_orders"]
    monthly["late_delivery_rate"] = (
        monthly["late_orders"].div(
            monthly["eligible_orders"].where(monthly["eligible_orders"] > 0)
        )
        * 100
    )

    monthly["on_time_delivery_rate"] = (
        monthly["on_time_orders"].div(
            monthly["eligible_orders"].where(monthly["eligible_orders"] > 0)
        )
        * 100
    )

    # Three-calendar-month rolling rate, weighted by order volume.
    rolling_late = monthly["late_orders"].rolling(window=3, min_periods=1).sum()

    rolling_eligible = monthly["eligible_orders"].rolling(window=3, min_periods=1).sum()

    monthly["rolling_3m_late_delivery_rate"] = (
        rolling_late.div(rolling_eligible.where(rolling_eligible > 0)) * 100
    )
    return monthly


def analyze_delivery_by_order_complexity(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare delivery performance across order-size and seller-count groups.
    """
    required_columns = {
        "order_id",
        "order_status",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "order_purchase_timestamp",
        "order_item_count",
        "distinct_sellers",
    }

    missing_columns = required_columns.difference(orders.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    eligible = (
        orders.loc[orders["order_status"].eq("delivered")]
        .dropna(
            subset=[
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]
        )
        .copy()
    )

    eligible["delivery_days"] = (
        eligible["order_delivered_customer_date"] - eligible["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    eligible["is_late"] = (
        eligible["order_delivered_customer_date"]
        > eligible["order_estimated_delivery_date"]
    )

    eligible["item_group"] = pd.cut(
        eligible["order_item_count"],
        bins=[0, 1, 2, 5, float("inf")],
        labels=["1 item", "2 items", "3–5 items", "6+ items"],
    )

    eligible["seller_group"] = pd.cut(
        eligible["distinct_sellers"],
        bins=[0, 1, 2, float("inf")],
        labels=["1 seller", "2 sellers", "3+ sellers"],
    )

    results = []

    for dimension, column in [
        ("Order size", "item_group"),
        ("Seller count", "seller_group"),
    ]:
        summary = (
            eligible.groupby(column, observed=True)
            .agg(
                eligible_orders=("order_id", "nunique"),
                late_orders=("is_late", "sum"),
                average_delivery_days=("delivery_days", "mean"),
                median_delivery_days=("delivery_days", "median"),
            )
            .reset_index()
            .rename(columns={column: "group"})
        )

        summary["late_delivery_rate"] = (
            summary["late_orders"] / summary["eligible_orders"] * 100
        )

        summary.insert(0, "dimension", dimension)
        results.append(summary)

    return pd.concat(results, ignore_index=True)
