import pandas as pd
import pytest

from boa.analytics.customers import (
    analyze_customer_cohorts,
    analyze_customer_recency,
    analyze_customer_segments,
    analyze_repeat_purchase_behavior,
)


@pytest.fixture
def sample_customers():
    return pd.DataFrame(
        {
            "customer_unique_id": [
                "customer_1",
                "customer_2",
                "customer_3",
                "customer_4",
                "customer_5",
                "customer_6",
            ],
            "recency_days": [10, 30, 90, 180, 365, 366],
            "frequency": [1, 1, 2, 1, 3, 2],
            "monetary": [100, 200, 300, 400, 500, 600],
            "customer_segment": [
                "Champions",
                "Loyal Customers",
                "Regular Customers",
                "At Risk",
                "Potential High Value",
                "Inactive / Hibernating",
            ],
        }
    )


@pytest.fixture
def sample_activity():
    return pd.DataFrame(
        [
            ("customer_a", "order_1", "2018-01-05"),
            ("customer_a", "order_2", "2018-01-15"),
            ("customer_a", "order_3", "2018-02-05"),
            ("customer_a", "order_4", "2018-03-05"),
            ("customer_b", "order_5", "2018-01-10"),
            ("customer_c", "order_6", "2018-02-10"),
            ("customer_c", "order_7", "2018-03-10"),
            ("customer_d", "order_8", "2018-03-15"),
        ],
        columns=[
            "customer_unique_id",
            "order_id",
            "order_purchase_timestamp",
        ],
    ).assign(
        order_purchase_timestamp=lambda df: pd.to_datetime(
            df["order_purchase_timestamp"]
        )
    )


def test_analyze_customer_segments(sample_customers):
    result = analyze_customer_segments(sample_customers)

    assert len(result) == 6
    assert result["customer_count"].sum() == 6
    assert result["total_orders"].sum() == 10
    assert result["total_customer_value"].sum() == 2100

    assert result.iloc[0]["customer_segment"] == "Inactive / Hibernating"
    assert result.iloc[0]["total_customer_value"] == 600

    assert result["customer_share"].sum() == pytest.approx(100.0)
    assert result["revenue_share"].sum() == pytest.approx(100.0)


def test_customer_segments_reject_duplicate_customers(sample_customers):
    duplicated = pd.concat(
        [sample_customers, sample_customers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per customer"):
        analyze_customer_segments(duplicated)


def test_customer_segments_reject_missing_segment(sample_customers):
    invalid = sample_customers.copy()
    invalid.loc[0, "customer_segment"] = None

    with pytest.raises(ValueError, match="cannot be missing"):
        analyze_customer_segments(invalid)


def test_customer_segments_reject_missing_columns(sample_customers):
    incomplete = sample_customers.drop(columns=["monetary"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_customer_segments(incomplete)


def test_analyze_repeat_purchase_behavior(sample_customers):
    result = analyze_repeat_purchase_behavior(sample_customers)

    one_time = result.set_index("purchase_group").loc["One-time customers"]
    repeat = result.set_index("purchase_group").loc["Repeat customers"]

    assert one_time["customer_count"] == 3
    assert one_time["delivered_orders"] == 3
    assert one_time["total_customer_value"] == 700
    assert one_time["avg_customer_value"] == pytest.approx(700 / 3)
    assert one_time["avg_order_value"] == pytest.approx(700 / 3)

    assert repeat["customer_count"] == 3
    assert repeat["delivered_orders"] == 7
    assert repeat["total_customer_value"] == 1400
    assert repeat["avg_customer_value"] == pytest.approx(1400 / 3)
    assert repeat["avg_order_value"] == pytest.approx((150 + 500 / 3 + 300) / 3)

    assert result["customer_share"].sum() == pytest.approx(100)
    assert result["revenue_share"].sum() == pytest.approx(100)


def test_repeat_purchase_rejects_duplicate_customers(sample_customers):
    duplicated = pd.concat(
        [sample_customers, sample_customers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per customer"):
        analyze_repeat_purchase_behavior(duplicated)


def test_repeat_purchase_rejects_non_positive_frequency(sample_customers):
    invalid = sample_customers.copy()
    invalid.loc[0, "frequency"] = 0

    with pytest.raises(ValueError, match="frequency must be positive"):
        analyze_repeat_purchase_behavior(invalid)


def test_repeat_purchase_rejects_missing_values(sample_customers):
    invalid = sample_customers.copy()
    invalid.loc[0, "monetary"] = None

    with pytest.raises(ValueError, match="cannot be missing"):
        analyze_repeat_purchase_behavior(invalid)


def test_analyze_customer_recency(sample_customers):
    result = analyze_customer_recency(sample_customers)

    assert result["customer_count"].sum() == 6
    assert result["total_customer_value"].sum() == 2100

    counts = result.set_index("recency_group")["customer_count"]

    assert counts["0–30 days"] == 2
    assert counts["31–90 days"] == 1
    assert counts["91–180 days"] == 1
    assert counts["181–365 days"] == 1
    assert counts["Over 365 days"] == 1

    assert result["customer_share"].sum() == pytest.approx(100)
    assert result["revenue_share"].sum() == pytest.approx(100)


def test_customer_recency_rejects_negative_recency(sample_customers):
    invalid = sample_customers.copy()
    invalid.loc[0, "recency_days"] = -1

    with pytest.raises(ValueError, match="Recency cannot be negative"):
        analyze_customer_recency(invalid)


def test_customer_recency_rejects_duplicate_customers(sample_customers):
    duplicated = pd.concat(
        [sample_customers, sample_customers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per customer"):
        analyze_customer_recency(duplicated)


def test_analyze_customer_cohorts(sample_activity):
    result = analyze_customer_cohorts(sample_activity)

    assert len(result) == 3
    assert result["cohort_month"].astype(str).tolist() == [
        "2018-01",
        "2018-02",
        "2018-03",
    ]

    january = result.set_index("cohort_month").loc[pd.Period("2018-01", freq="M")]
    february = result.set_index("cohort_month").loc[pd.Period("2018-02", freq="M")]
    march = result.set_index("cohort_month").loc[pd.Period("2018-03", freq="M")]

    assert january["cohort_size"] == 2
    assert january["month_0"] == pytest.approx(100)
    assert january["month_1"] == pytest.approx(50)
    assert january["month_2"] == pytest.approx(50)

    assert february["cohort_size"] == 1
    assert february["month_0"] == pytest.approx(100)
    assert february["month_1"] == pytest.approx(100)
    assert pd.isna(february["month_2"])

    assert march["cohort_size"] == 1
    assert march["month_0"] == pytest.approx(100)
    assert pd.isna(march["month_1"])
    assert pd.isna(march["month_2"])


def test_customer_cohorts_reject_empty_data():
    empty = pd.DataFrame(
        columns=[
            "customer_unique_id",
            "order_id",
            "order_purchase_timestamp",
        ]
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        analyze_customer_cohorts(empty)


def test_customer_cohorts_reject_duplicate_orders(sample_activity):
    duplicated = pd.concat(
        [sample_activity, sample_activity.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per delivered order"):
        analyze_customer_cohorts(duplicated)


def test_customer_cohorts_reject_missing_values(sample_activity):
    invalid = sample_activity.copy()
    invalid.loc[0, "customer_unique_id"] = None

    with pytest.raises(ValueError, match="missing values"):
        analyze_customer_cohorts(invalid)


def test_customer_cohorts_reject_missing_columns(sample_activity):
    incomplete = sample_activity.drop(columns=["order_id"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_customer_cohorts(incomplete)
