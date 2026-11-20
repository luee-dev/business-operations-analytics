import pandas as pd
import pytest

from boa.analytics.sellers import (
    analyze_seller_operational_risk,
    analyze_seller_performance,
    summarize_seller_concentration,
)


@pytest.fixture
def sample_sellers():
    return pd.DataFrame(
        [
            {
                "seller_id": "seller_a",
                "seller_city": "Nairobi",
                "seller_state": "KE",
                "total_order_associations": 100,
                "delivered_order_associations": 90,
                "canceled_order_associations": 5,
                "distinct_customers": 80,
                "distinct_products_sold": 10,
                "delivered_product_value": 9000.0,
                "delivered_item_lines": 100,
                "shipping_deadline_eligible_item_lines": 100,
                "delivered_order_percentage": 90.0,
                "canceled_order_percentage": 5.0,
                "delivery_estimate_eligible_orders": 100,
                "late_delivery_order_associations": 20,
                "average_delivered_order_value": 100.0,
                "avg_purchase_to_carrier_days": 2.0,
                "avg_carrier_to_customer_days": 5.0,
                "avg_total_delivery_days": 7.0,
                "median_total_delivery_days": 6.0,
                "p90_total_delivery_days": 12.0,
                "late_delivery_percentage": 20.0,
                "on_time_delivery_percentage": 80.0,
                "delivered_value_per_order_association": 100.0,
                "shipping_deadline_late_percentage": 10.0,
            },
            {
                "seller_id": "seller_b",
                "seller_city": "Mombasa",
                "seller_state": "KE",
                "total_order_associations": 80,
                "delivered_order_associations": 70,
                "canceled_order_associations": 8,
                "distinct_customers": 60,
                "distinct_products_sold": 20,
                "delivered_product_value": 7000.0,
                "delivered_item_lines": 80,
                "shipping_deadline_eligible_item_lines": 80,
                "delivered_order_percentage": 87.5,
                "canceled_order_percentage": 10.0,
                "delivery_estimate_eligible_orders": 80,
                "late_delivery_order_associations": 8,
                "average_delivered_order_value": 100.0,
                "avg_purchase_to_carrier_days": 1.5,
                "avg_carrier_to_customer_days": 4.0,
                "avg_total_delivery_days": 5.5,
                "median_total_delivery_days": 5.0,
                "p90_total_delivery_days": 9.0,
                "late_delivery_percentage": 10.0,
                "on_time_delivery_percentage": 90.0,
                "delivered_value_per_order_association": 100.0,
                "shipping_deadline_late_percentage": 5.0,
            },
            {
                "seller_id": "seller_c",
                "seller_city": "Kisumu",
                "seller_state": "KE",
                "total_order_associations": 0,
                "delivered_order_associations": 0,
                "canceled_order_associations": 0,
                "distinct_customers": 0,
                "distinct_products_sold": 0,
                "delivered_product_value": 0.0,
                "delivered_item_lines": 0,
                "shipping_deadline_eligible_item_lines": 0,
                "delivered_order_percentage": 0.0,
                "canceled_order_percentage": 0.0,
                "delivery_estimate_eligible_orders": 0,
                "late_delivery_order_associations": 0,
                "average_delivered_order_value": float("nan"),
                "avg_purchase_to_carrier_days": float("nan"),
                "avg_carrier_to_customer_days": float("nan"),
                "avg_total_delivery_days": float("nan"),
                "median_total_delivery_days": float("nan"),
                "p90_total_delivery_days": float("nan"),
                "late_delivery_percentage": float("nan"),
                "on_time_delivery_percentage": float("nan"),
                "delivered_value_per_order_association": float("nan"),
                "shipping_deadline_late_percentage": float("nan"),
            },
        ]
    )


@pytest.fixture
def risk_sellers():
    return pd.DataFrame(
        [
            {
                "seller_id": "seller_a",
                "seller_city": "Nairobi",
                "seller_state": "KE",
                "delivery_estimate_eligible_orders": 100,
                "late_delivery_order_associations": 40,
                "delivered_product_value": 10000.0,
            },
            {
                "seller_id": "seller_b",
                "seller_city": "Mombasa",
                "seller_state": "KE",
                "delivery_estimate_eligible_orders": 100,
                "late_delivery_order_associations": 10,
                "delivered_product_value": 8000.0,
            },
            {
                "seller_id": "seller_c",
                "seller_city": "Kisumu",
                "seller_state": "KE",
                "delivery_estimate_eligible_orders": 20,
                "late_delivery_order_associations": 2,
                "delivered_product_value": 2000.0,
            },
        ]
    )


def test_analyze_seller_performance(sample_sellers):
    result = analyze_seller_performance(sample_sellers)

    assert len(result) == 3
    assert result["seller_id"].tolist() == [
        "seller_a",
        "seller_b",
        "seller_c",
    ]

    assert result["revenue_share"].sum() == pytest.approx(100)

    seller_a = result.iloc[0]

    assert seller_a["revenue_share"] == pytest.approx(56.25)
    assert seller_a["revenue_per_product"] == pytest.approx(900)
    assert seller_a["revenue_per_customer"] == pytest.approx(112.5)
    assert seller_a["items_per_delivered_association"] == pytest.approx(100 / 90)
    assert seller_a["revenue_rank"] == 1

    assert result["revenue_rank"].tolist() == [1, 2, 3]
    assert result["cumulative_revenue_share"].iloc[-1] == pytest.approx(100)


def test_seller_performance_preserves_undefined_metrics(sample_sellers):
    result = analyze_seller_performance(sample_sellers)

    seller_c = result.set_index("seller_id").loc["seller_c"]

    assert pd.isna(seller_c["revenue_per_product"])
    assert pd.isna(seller_c["revenue_per_customer"])
    assert pd.isna(seller_c["items_per_delivered_association"])


def test_seller_performance_rejects_duplicate_sellers(sample_sellers):
    duplicated = pd.concat(
        [sample_sellers, sample_sellers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per seller"):
        analyze_seller_performance(duplicated)


def test_seller_performance_rejects_missing_columns(sample_sellers):
    incomplete = sample_sellers.drop(columns=["seller_city"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_seller_performance(incomplete)


def test_seller_performance_rejects_unexpected_missing_values(
    sample_sellers,
):
    invalid = sample_sellers.copy()
    invalid.loc[0, "seller_city"] = None

    with pytest.raises(
        ValueError,
        match="Unexpected missing values in required seller fields",
    ):
        analyze_seller_performance(invalid)


def test_seller_performance_rejects_missing_metrics_for_active_seller(
    sample_sellers,
):
    invalid = sample_sellers.copy()
    invalid.loc[0, "avg_total_delivery_days"] = None

    with pytest.raises(
        ValueError,
        match="Unexpected missing delivery metrics",
    ):
        analyze_seller_performance(invalid)


def test_seller_performance_rejects_missing_shipping_rate(
    sample_sellers,
):
    invalid = sample_sellers.copy()
    invalid.loc[0, "shipping_deadline_late_percentage"] = None

    with pytest.raises(
        ValueError,
        match="Missing shipping-deadline rate",
    ):
        analyze_seller_performance(invalid)


def test_seller_performance_rejects_zero_total_revenue(sample_sellers):
    invalid = sample_sellers.copy()
    invalid["delivered_product_value"] = 0

    with pytest.raises(ValueError, match="Total delivered revenue"):
        analyze_seller_performance(invalid)


def test_summarize_seller_concentration(sample_sellers):
    result = summarize_seller_concentration(sample_sellers)

    assert result["total_sellers"] == 3
    assert result["sellers_with_delivered_sales"] == 2
    assert result["sellers_without_delivered_sales"] == 1

    assert result["total_delivered_product_value"] == 16000

    assert result["top_10_revenue_share"] == pytest.approx(100)
    assert result["top_20_revenue_share"] == pytest.approx(100)
    assert result["top_50_revenue_share"] == pytest.approx(100)

    expected_hhi = 56.25**2 + 43.75**2

    assert result["seller_revenue_hhi"] == pytest.approx(expected_hhi)

    assert result["top_10_seller_ids"] == [
        "seller_a",
        "seller_b",
    ]


def test_seller_concentration_rejects_duplicate_sellers(sample_sellers):
    duplicated = pd.concat(
        [sample_sellers, sample_sellers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per seller"):
        summarize_seller_concentration(duplicated)


def test_seller_concentration_rejects_negative_revenue(sample_sellers):
    invalid = sample_sellers.copy()
    invalid.loc[0, "delivered_product_value"] = -100

    with pytest.raises(ValueError, match="negative values"):
        summarize_seller_concentration(invalid)


def test_seller_concentration_rejects_missing_revenue(sample_sellers):
    invalid = sample_sellers.copy()
    invalid.loc[0, "delivered_product_value"] = None

    with pytest.raises(ValueError, match="missing values"):
        summarize_seller_concentration(invalid)


def test_seller_concentration_rejects_zero_total_revenue(sample_sellers):
    invalid = sample_sellers.copy()
    invalid["delivered_product_value"] = 0

    with pytest.raises(ValueError, match="must be positive"):
        summarize_seller_concentration(invalid)


def test_analyze_seller_operational_risk(risk_sellers):
    result = analyze_seller_operational_risk(risk_sellers)

    assert len(result) == 2

    # Benchmark uses only the two eligible sellers:
    # (40 + 10) / (100 + 100) = 25%.
    assert result["benchmark_rate"].unique().tolist() == pytest.approx([0.25])

    seller_a = result.set_index("seller_id").loc["seller_a"]
    seller_b = result.set_index("seller_id").loc["seller_b"]

    assert seller_a["late_delivery_rate"] == pytest.approx(0.40)
    assert seller_b["late_delivery_rate"] == pytest.approx(0.10)

    assert seller_a["expected_late_associations"] == pytest.approx(25)
    assert seller_a["excess_late_associations"] == pytest.approx(15)

    assert seller_b["expected_late_associations"] == pytest.approx(25)
    assert seller_b["excess_late_associations"] == pytest.approx(-15)

    assert seller_a["revenue_share"] == pytest.approx(50)
    assert seller_b["revenue_share"] == pytest.approx(40)

    assert seller_a["operational_risk"] == "Elevated"
    assert seller_b["operational_risk"] == "Not statistically elevated"


def test_seller_operational_risk_excludes_insufficient_observations(
    risk_sellers,
):
    result = analyze_seller_operational_risk(
        risk_sellers,
        minimum_eligible=30,
    )

    assert "seller_c" not in result["seller_id"].tolist()


def test_seller_operational_risk_rejects_no_eligible_sellers(risk_sellers):
    with pytest.raises(
        ValueError,
        match="No sellers meet the minimum eligibility threshold",
    ):
        analyze_seller_operational_risk(
            risk_sellers,
            minimum_eligible=200,
        )


def test_seller_operational_risk_rejects_invalid_late_counts(risk_sellers):
    invalid = risk_sellers.copy()
    invalid.loc[0, "late_delivery_order_associations"] = 101

    with pytest.raises(ValueError, match="Invalid late-delivery"):
        analyze_seller_operational_risk(invalid)


def test_seller_operational_risk_rejects_missing_columns(risk_sellers):
    incomplete = risk_sellers.drop(columns=["seller_state"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_seller_operational_risk(incomplete)


def test_seller_operational_risk_rejects_zero_total_revenue(risk_sellers):
    invalid = risk_sellers.copy()
    invalid["delivered_product_value"] = 0

    with pytest.raises(ValueError, match="Total delivered revenue"):
        analyze_seller_operational_risk(invalid)
