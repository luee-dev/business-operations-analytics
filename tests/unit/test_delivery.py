import pandas as pd
import pytest

from boa.analytics.delivery import (
    analyze_delivery_by_order_complexity,
    analyze_delivery_performance,
    analyze_monthly_delivery_performance,
)


@pytest.fixture
def sample_orders():
    return pd.DataFrame(
        [
            {
                "order_id": "order_1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01",
                "order_delivered_customer_date": "2018-01-03",
                "order_estimated_delivery_date": "2018-01-02",
                "order_item_count": 1,
                "distinct_sellers": 1,
            },
            {
                "order_id": "order_2",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-10",
                "order_delivered_customer_date": "2018-01-12",
                "order_estimated_delivery_date": "2018-01-12",
                "order_item_count": 2,
                "distinct_sellers": 1,
            },
            {
                "order_id": "order_3",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-02-01",
                "order_delivered_customer_date": "2018-02-05",
                "order_estimated_delivery_date": "2018-02-06",
                "order_item_count": 3,
                "distinct_sellers": 2,
            },
            {
                "order_id": "order_4",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-02-10",
                "order_delivered_customer_date": "2018-02-12",
                "order_estimated_delivery_date": "2018-02-11",
                "order_item_count": 6,
                "distinct_sellers": 3,
            },
            {
                "order_id": "order_5",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-03-01",
                "order_delivered_customer_date": None,
                "order_estimated_delivery_date": "2018-03-05",
                "order_item_count": 1,
                "distinct_sellers": 1,
            },
            {
                "order_id": "order_6",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-03-05",
                "order_delivered_customer_date": None,
                "order_estimated_delivery_date": "2018-03-10",
                "order_item_count": 1,
                "distinct_sellers": 1,
            },
            {
                "order_id": "order_7",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-03-10",
                "order_delivered_customer_date": "2018-03-12",
                "order_estimated_delivery_date": None,
                "order_item_count": 2,
                "distinct_sellers": 2,
            },
        ]
    ).assign(
        order_purchase_timestamp=lambda df: pd.to_datetime(
            df["order_purchase_timestamp"]
        ),
        order_delivered_customer_date=lambda df: pd.to_datetime(
            df["order_delivered_customer_date"]
        ),
        order_estimated_delivery_date=lambda df: pd.to_datetime(
            df["order_estimated_delivery_date"]
        ),
    )


def test_analyze_delivery_performance(sample_orders):
    result = analyze_delivery_performance(sample_orders)

    assert result["total_orders"] == 7
    assert result["delivered_orders"] == 6
    assert result["eligible_orders"] == 4
    assert result["late_orders"] == 2
    assert result["on_time_orders"] == 2
    assert result["delivered_missing_timestamps"] == 2

    assert result["late_delivery_rate"] == pytest.approx(50.0)
    assert result["on_time_delivery_rate"] == pytest.approx(50.0)

    assert result["average_delivery_days"] == pytest.approx(2.5)
    assert result["median_delivery_days"] == pytest.approx(2.0)
    assert result["average_delivery_variance_days"] == pytest.approx(0.25)
    assert result["p90_delivery_days"] == pytest.approx(3.4)


def test_delivery_performance_excludes_non_delivered_orders(sample_orders):
    result = analyze_delivery_performance(sample_orders)

    assert result["eligible_orders"] == 4
    assert result["delivered_orders"] == 6


def test_delivery_performance_rejects_missing_columns(sample_orders):
    incomplete = sample_orders.drop(columns=["order_id"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_delivery_performance(incomplete)


def test_monthly_delivery_performance(sample_orders):
    result = analyze_monthly_delivery_performance(sample_orders)

    assert result["purchase_month"].tolist() == [
        "2018-01",
        "2018-02",
        "2018-03",
    ]

    assert result["eligible_orders"].tolist() == [2, 2, 0]
    assert result["late_orders"].tolist() == [1, 1, 0]
    assert result["on_time_orders"].tolist() == [1, 1, 0]

    assert result.loc[0, "late_delivery_rate"] == pytest.approx(50.0)
    assert result.loc[1, "late_delivery_rate"] == pytest.approx(50.0)

    assert pd.isna(result.loc[2, "late_delivery_rate"])
    assert pd.isna(result.loc[2, "on_time_delivery_rate"])

    # January and February: 2 late orders out of 4 eligible orders.
    # March adds no eligible orders.
    assert result.loc[2, "rolling_3m_late_delivery_rate"] == pytest.approx(50.0)


def test_monthly_delivery_performance_rejects_missing_columns(sample_orders):
    incomplete = sample_orders.drop(columns=["order_id"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_monthly_delivery_performance(incomplete)


def test_delivery_by_order_complexity(sample_orders):
    result = analyze_delivery_by_order_complexity(sample_orders)

    item_groups = result.loc[result["dimension"] == "Order size"].set_index("group")

    assert item_groups.loc["1 item", "eligible_orders"] == 1
    assert item_groups.loc["1 item", "late_orders"] == 1

    assert item_groups.loc["2 items", "eligible_orders"] == 1
    assert item_groups.loc["2 items", "late_orders"] == 0

    assert item_groups.loc["3–5 items", "eligible_orders"] == 1
    assert item_groups.loc["3–5 items", "late_orders"] == 0

    assert item_groups.loc["6+ items", "eligible_orders"] == 1
    assert item_groups.loc["6+ items", "late_orders"] == 1

    seller_groups = result.loc[result["dimension"] == "Seller count"].set_index("group")

    assert seller_groups.loc["1 seller", "eligible_orders"] == 2
    assert seller_groups.loc["1 seller", "late_orders"] == 1

    assert seller_groups.loc["2 sellers", "eligible_orders"] == 1
    assert seller_groups.loc["2 sellers", "late_orders"] == 0

    assert seller_groups.loc["3+ sellers", "eligible_orders"] == 1
    assert seller_groups.loc["3+ sellers", "late_orders"] == 1


def test_delivery_by_order_complexity_rejects_missing_columns(sample_orders):
    incomplete = sample_orders.drop(columns=["distinct_sellers"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_delivery_by_order_complexity(incomplete)
