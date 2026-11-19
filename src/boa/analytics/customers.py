import pandas as pd


def analyze_customer_segments(customers: pd.DataFrame) -> pd.DataFrame:
    """
    Summarise customer value, purchasing frequency and recency
    across RFM customer segments.
    """
    required_columns = {
        "customer_unique_id",
        "recency_days",
        "frequency",
        "monetary",
        "customer_segment",
    }

    missing_columns = required_columns.difference(customers.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if customers["customer_unique_id"].duplicated().any():
        raise ValueError("Expected one row per customer.")

    if customers["customer_segment"].isna().any():
        raise ValueError("Customer segments cannot be missing.")

    summary = (
        customers.groupby("customer_segment")
        .agg(
            customer_count=("customer_unique_id", "nunique"),
            total_orders=("frequency", "sum"),
            total_customer_value=("monetary", "sum"),
            avg_customer_value=("monetary", "mean"),
            median_recency_days=("recency_days", "median"),
            avg_frequency=("frequency", "mean"),
        )
        .reset_index()
        .sort_values("total_customer_value", ascending=False)
        .reset_index(drop=True)
    )

    total_customers = summary["customer_count"].sum()

    summary["customer_share"] = (
        summary["customer_count"] / total_customers * 100
    )

    summary["revenue_share"] = (
        summary["total_customer_value"]
        / summary["total_customer_value"].sum()
        * 100
    )

    return summary

def analyze_repeat_purchase_behavior(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare one-time and repeat customers by purchasing behaviour.
    """
    required_columns = {
        "customer_unique_id",
        "frequency",
        "monetary",
    }

    missing_columns = required_columns.difference(customers.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if customers["customer_unique_id"].duplicated().any():
        raise ValueError("Expected one row per customer.")

    if customers[["frequency", "monetary"]].isna().any().any():
        raise ValueError("Frequency and monetary values cannot be missing.")

    if (customers["frequency"] <= 0).any():
        raise ValueError("Customer frequency must be positive.")

    data = customers.copy()

    data["purchase_group"] = data["frequency"].map(
        lambda frequency: (
            "One-time customers"
            if frequency == 1
            else "Repeat customers"
        )
    )

    data["average_order_value"] = (
        data["monetary"] / data["frequency"]
    )

    summary = (
        data.groupby("purchase_group")
        .agg(
            customer_count=("customer_unique_id", "nunique"),
            delivered_orders=("frequency", "sum"),
            total_customer_value=("monetary", "sum"),
            avg_customer_value=("monetary", "mean"),
            avg_order_value=("average_order_value", "mean"),
        )
        .reset_index()
    )

    summary["customer_share"] = (
        summary["customer_count"]
        / summary["customer_count"].sum()
        * 100
    )

    summary["revenue_share"] = (
        summary["total_customer_value"]
        / summary["total_customer_value"].sum()
        * 100
    )

    return summary


def analyze_customer_recency(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Group customers by days since their most recent purchase.
    """
    required_columns = {
        "customer_unique_id",
        "recency_days",
        "monetary",
    }

    missing_columns = required_columns.difference(customers.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if customers["customer_unique_id"].duplicated().any():
        raise ValueError("Expected one row per customer.")

    if customers[["recency_days", "monetary"]].isna().any().any():
        raise ValueError("Recency and monetary values cannot be missing.")

    if (customers["recency_days"] < 0).any():
        raise ValueError("Recency cannot be negative.")

    data = customers.copy()

    data["recency_group"] = pd.cut(
        data["recency_days"],
        bins=[-1, 30, 90, 180, 365, float("inf")],
        labels=[
            "0–30 days",
            "31–90 days",
            "91–180 days",
            "181–365 days",
            "Over 365 days",
        ],
    )

    summary = (
        data.groupby("recency_group", observed=True)
        .agg(
            customer_count=("customer_unique_id", "nunique"),
            total_customer_value=("monetary", "sum"),
            avg_customer_value=("monetary", "mean"),
            median_recency_days=("recency_days", "median"),
        )
        .reset_index()
    )

    summary["customer_share"] = (
        summary["customer_count"]
        / summary["customer_count"].sum()
        * 100
    )

    summary["revenue_share"] = (
        summary["total_customer_value"]
        / summary["total_customer_value"].sum()
        * 100
    )

    return summary

def analyze_customer_cohorts(
    activity: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate monthly customer activity retention by first
    delivered-purchase cohort.

    Zero means the cohort had no active customers in an observed
    month. NaN means the month is outside the observation window.
    """
    required_columns = {
        "customer_unique_id",
        "order_id",
        "order_purchase_timestamp",
    }

    missing_columns = required_columns.difference(activity.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if activity.empty:
        raise ValueError("Customer activity data cannot be empty.")

    if activity[list(required_columns)].isna().any().any():
        raise ValueError("Customer activity contains missing values.")

    if activity["order_id"].duplicated().any():
        raise ValueError("Expected one row per delivered order.")

    data = activity.copy()

    purchase_dates = data["order_purchase_timestamp"].dt.tz_localize(None)
    data["activity_month"] = purchase_dates.dt.to_period("M")

    first_purchase = (
        data.groupby("customer_unique_id")["activity_month"]
        .min()
        .rename("cohort_month")
    )

    data = data.join(first_purchase, on="customer_unique_id")

    data = data.drop_duplicates(
        subset=["customer_unique_id", "activity_month"]
    )

    data["cohort_index"] = (
        (data["activity_month"].dt.year - data["cohort_month"].dt.year)
        * 12
        + data["activity_month"].dt.month
        - data["cohort_month"].dt.month
    )

    cohort_sizes = (
        first_purchase.value_counts().sort_index().rename("cohort_size")
    )

    active_customers = (
        data.groupby(["cohort_month", "cohort_index"])
        ["customer_unique_id"]
        .nunique()
        .unstack("cohort_index")
    )

    max_observed_month = data["activity_month"].max()

    max_cohort_index = (
        (max_observed_month.year - data["cohort_month"].min().year) * 12
        + max_observed_month.month
        - data["cohort_month"].min().month
    )

    # Create every relative month and treat missing activity as zero.
    active_customers = (
        active_customers
        .reindex(columns=range(max_cohort_index + 1))
        .fillna(0)
    )

    retention = active_customers.div(cohort_sizes, axis=0) * 100

    # Mask months that fall beyond the observation window.
    for row_number, cohort_month in enumerate(retention.index):
        cohort_age = (
            (max_observed_month.year - cohort_month.year) * 12
            + max_observed_month.month
            - cohort_month.month
        )

        retention.iloc[row_number, cohort_age + 1:] = float("nan")

    retention.columns = [
        f"month_{int(month)}" for month in retention.columns
    ]

    retention.insert(0, "cohort_size", cohort_sizes)
    retention.index.name = "cohort_month"

    return retention.reset_index()