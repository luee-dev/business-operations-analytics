import numpy as np
import pandas as pd
import pytest

from boa.analytics.customer_experience import (
    analyze_customer_experience,
)


@pytest.fixture
def sample_orders():
    return pd.DataFrame(
        [
            {
                "order_id": "order_1",
                "order_status": "delivered",
                "is_late_delivery": True,
                "delivery_days": 20.0,
                "average_review_score": 1.0,
                "scored_review_records": 2,
                "negative_review_records": 2,
            },
            {
                "order_id": "order_2",
                "order_status": "delivered",
                "is_late_delivery": True,
                "delivery_days": 15.0,
                "average_review_score": 2.0,
                "scored_review_records": 1,
                "negative_review_records": 1,
            },
            {
                "order_id": "order_3",
                "order_status": "delivered",
                "is_late_delivery": False,
                "delivery_days": 8.0,
                "average_review_score": 5.0,
                "scored_review_records": 1,
                "negative_review_records": 0,
            },
            {
                "order_id": "order_4",
                "order_status": "delivered",
                "is_late_delivery": False,
                "delivery_days": 10.0,
                "average_review_score": 4.0,
                "scored_review_records": 2,
                "negative_review_records": 0,
            },
            {
                "order_id": "order_5",
                "order_status": "delivered",
                "is_late_delivery": False,
                "delivery_days": 12.0,
                "average_review_score": 3.0,
                "scored_review_records": 1,
                "negative_review_records": 1,
            },
            {
                "order_id": "order_6",
                "order_status": "canceled",
                "is_late_delivery": None,
                "delivery_days": None,
                "average_review_score": 1.0,
                "scored_review_records": 1,
                "negative_review_records": 1,
            },
            {
                "order_id": "order_7",
                "order_status": "delivered",
                "is_late_delivery": True,
                "delivery_days": 18.0,
                "average_review_score": None,
                "scored_review_records": 1,
                "negative_review_records": 1,
            },
            {
                "order_id": "order_8",
                "order_status": "delivered",
                "is_late_delivery": False,
                "delivery_days": 9.0,
                "average_review_score": None,
                "scored_review_records": 0,
                "negative_review_records": 0,
            },
        ]
    )


def test_analyze_customer_experience(sample_orders):
    result = analyze_customer_experience(sample_orders)

    assert result["eligible_orders"] == 5

    assert result["late"]["orders"] == 2
    assert result["on_time"]["orders"] == 3

    assert result["late"]["average_review_score"] == pytest.approx(1.5)
    assert result["on_time"]["average_review_score"] == pytest.approx(4.0)

    assert result["late"]["median_review_score"] == pytest.approx(1.5)
    assert result["on_time"]["median_review_score"] == pytest.approx(4.0)

    assert result["late"]["average_delivery_days"] == pytest.approx(17.5)
    assert result["on_time"]["average_delivery_days"] == pytest.approx(10.0)

    assert result["differences"]["average_review_score"] == pytest.approx(-2.5)


def test_customer_experience_excludes_ineligible_orders(sample_orders):
    result = analyze_customer_experience(sample_orders)

    # Excludes canceled orders, missing review scores,
    # and orders without scored reviews.
    assert result["eligible_orders"] == 5


def test_negative_review_order_rate_counts_each_order_once(sample_orders):
    result = analyze_customer_experience(sample_orders)

    # Two late orders both have negative reviews.
    assert result["late"]["negative_review_orders"] == 2
    assert result["late"]["negative_review_order_rate"] == pytest.approx(1)

    # One of three on-time orders has at least one negative review.
    assert result["on_time"]["negative_review_orders"] == 1
    assert result["on_time"]["negative_review_order_rate"] == pytest.approx(1 / 3)


def test_review_record_metrics_are_separate_from_order_metrics(
    sample_orders,
):
    result = analyze_customer_experience(sample_orders)

    assert result["late"]["scored_review_records"] == 3
    assert result["late"]["negative_review_records"] == 3
    assert result["late"]["negative_review_record_rate"] == pytest.approx(1)

    assert result["on_time"]["scored_review_records"] == 4
    assert result["on_time"]["negative_review_records"] == 1
    assert result["on_time"]["negative_review_record_rate"] == pytest.approx(0.25)


def test_customer_experience_returns_statistical_tests(sample_orders):
    result = analyze_customer_experience(sample_orders)

    tests = result["statistical_tests"]

    expected_tests = {
        "welch_t_test_review_score",
        "two_proportion_z_test_negative_review_orders",
        "mann_whitney_u_review_score",
    }

    assert set(tests) == expected_tests

    for test_result in tests.values():
        assert np.isfinite(test_result["statistic"])
        assert np.isfinite(test_result["p_value"])
        assert 0 <= test_result["p_value"] <= 1


def test_customer_experience_returns_welch_degrees_of_freedom(
    sample_orders,
):
    result = analyze_customer_experience(sample_orders)

    degrees_freedom = result["statistical_tests"]["welch_t_test_review_score"][
        "degrees_freedom"
    ]

    assert np.isfinite(degrees_freedom)
    assert degrees_freedom > 0


def test_customer_experience_rejects_duplicate_orders(sample_orders):
    duplicated = pd.concat(
        [sample_orders, sample_orders.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicate order_id"):
        analyze_customer_experience(duplicated)


def test_customer_experience_rejects_missing_columns(sample_orders):
    incomplete = sample_orders.drop(columns=["average_review_score"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_customer_experience(incomplete)


def test_customer_experience_rejects_invalid_delivery_classification(
    sample_orders,
):
    invalid = sample_orders.copy()
    invalid["is_late_delivery"] = invalid["is_late_delivery"].astype(object)
    invalid.loc[0, "is_late_delivery"] = "late"

    with pytest.raises(TypeError, match="only boolean values or nulls"):
        analyze_customer_experience(invalid)


def test_customer_experience_rejects_negative_review_counts(
    sample_orders,
):
    invalid = sample_orders.copy()
    invalid.loc[0, "negative_review_records"] = -1

    with pytest.raises(ValueError, match="cannot be negative"):
        analyze_customer_experience(invalid)


def test_customer_experience_rejects_no_eligible_orders(sample_orders):
    invalid = sample_orders.copy()
    invalid["order_status"] = "canceled"

    with pytest.raises(
        ValueError,
        match="No eligible delivered orders with scored reviews",
    ):
        analyze_customer_experience(invalid)


def test_customer_experience_requires_both_delivery_groups(sample_orders):
    invalid = sample_orders.copy()
    invalid["is_late_delivery"] = False

    with pytest.raises(
        ValueError,
        match="Both late and on-time groups must contain observations",
    ):
        analyze_customer_experience(invalid)
