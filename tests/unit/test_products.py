import pandas as pd
import pytest

from boa.analytics.products import (
    analyze_category_concentration,
    analyze_category_performance,
    analyze_product_performance,
    summarize_product_concentration,
)


@pytest.fixture
def sample_categories():
    return pd.DataFrame(
        [
            {
                "product_category": "electronics",
                "total_products": 10,
                "total_order_item_lines": 100,
                "total_orders": 90,
                "delivered_item_lines": 90,
                "delivered_orders": 85,
                "canceled_orders": 5,
                "delivered_product_value": 9000.0,
                "average_delivered_item_price": 100.0,
            },
            {
                "product_category": "furniture",
                "total_products": 20,
                "total_order_item_lines": 80,
                "total_orders": 75,
                "delivered_item_lines": 70,
                "delivered_orders": 65,
                "canceled_orders": 10,
                "delivered_product_value": 7000.0,
                "average_delivered_item_price": 100.0,
            },
            {
                "product_category": "books",
                "total_products": 30,
                "total_order_item_lines": 60,
                "total_orders": 55,
                "delivered_item_lines": 50,
                "delivered_orders": 48,
                "canceled_orders": 5,
                "delivered_product_value": 3000.0,
                "average_delivered_item_price": 60.0,
            },
        ]
    )


@pytest.fixture
def sample_products():
    return pd.DataFrame(
        [
            {
                "product_id": "product_a",
                "product_category": "electronics",
                "total_orders": 50,
                "distinct_sellers": 2,
                "delivered_item_lines": 60,
                "delivered_product_value": 6000.0,
                "average_delivered_item_price": 100.0,
            },
            {
                "product_id": "product_b",
                "product_category": "furniture",
                "total_orders": 30,
                "distinct_sellers": 1,
                "delivered_item_lines": 30,
                "delivered_product_value": 3000.0,
                "average_delivered_item_price": 100.0,
            },
            {
                "product_id": "product_c",
                "product_category": "books",
                "total_orders": 10,
                "distinct_sellers": 3,
                "delivered_item_lines": 10,
                "delivered_product_value": 1000.0,
                "average_delivered_item_price": 100.0,
            },
            {
                "product_id": "product_d",
                "product_category": "books",
                "total_orders": 0,
                "distinct_sellers": 0,
                "delivered_item_lines": 0,
                "delivered_product_value": 0.0,
                "average_delivered_item_price": 0.0,
            },
        ]
    )


def test_analyze_category_performance(sample_categories):
    result = analyze_category_performance(sample_categories)

    assert len(result) == 3
    assert result.iloc[0]["product_category"] == "electronics"

    assert result["delivered_product_value"].sum() == 19000
    assert result["revenue_share"].sum() == pytest.approx(100)

    electronics = result.iloc[0]

    assert electronics["revenue_share"] == pytest.approx(9000 / 19000 * 100)
    assert electronics["revenue_per_catalogue_product"] == pytest.approx(900)
    assert electronics["cancellation_rate"] == pytest.approx(5 / 90 * 100)


def test_category_performance_rejects_duplicate_categories(
    sample_categories,
):
    duplicated = pd.concat(
        [sample_categories, sample_categories.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per product category"):
        analyze_category_performance(duplicated)


def test_category_performance_rejects_missing_values(sample_categories):
    invalid = sample_categories.copy()
    invalid.loc[0, "delivered_product_value"] = None

    with pytest.raises(ValueError, match="contains missing values"):
        analyze_category_performance(invalid)


def test_category_performance_rejects_missing_columns(sample_categories):
    incomplete = sample_categories.drop(columns=["total_products"])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_category_performance(incomplete)


def test_analyze_category_concentration(sample_categories):
    result = analyze_category_concentration(sample_categories)

    assert result["top_5_revenue_share"] == pytest.approx(100)
    assert result["top_10_revenue_share"] == pytest.approx(100)

    expected_hhi = (
        (9000 / 19000 * 100) ** 2
        + (7000 / 19000 * 100) ** 2
        + (3000 / 19000 * 100) ** 2
    )

    assert result["category_hhi"] == pytest.approx(expected_hhi)

    assert len(result["top_categories"]) == 3
    assert len(result["highest_productivity"]) == 3
    assert len(result["lowest_productivity"]) == 3

    assert result["highest_productivity"].iloc[0]["product_category"] == "electronics"


def test_analyze_product_performance(sample_products):
    result = analyze_product_performance(sample_products)

    assert result["product_id"].tolist() == [
        "product_a",
        "product_b",
        "product_c",
        "product_d",
    ]

    assert result["revenue_rank"].tolist() == [1, 2, 3, 4]

    assert result.iloc[0]["revenue_share"] == pytest.approx(60)
    assert result.iloc[1]["revenue_share"] == pytest.approx(30)
    assert result.iloc[2]["revenue_share"] == pytest.approx(10)
    assert result.iloc[3]["revenue_share"] == pytest.approx(0)

    assert result["cumulative_revenue_share"].tolist() == pytest.approx(
        [60, 90, 100, 100]
    )


def test_product_performance_rejects_duplicate_products(sample_products):
    duplicated = pd.concat(
        [sample_products, sample_products.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per product"):
        analyze_product_performance(duplicated)


def test_product_performance_rejects_negative_revenue(sample_products):
    invalid = sample_products.copy()
    invalid.loc[0, "delivered_product_value"] = -100

    with pytest.raises(ValueError, match="cannot be negative"):
        analyze_product_performance(invalid)


def test_product_performance_rejects_zero_total_revenue(sample_products):
    invalid = sample_products.copy()
    invalid["delivered_product_value"] = 0

    with pytest.raises(ValueError, match="must be positive"):
        analyze_product_performance(invalid)


def test_product_performance_rejects_missing_values(sample_products):
    invalid = sample_products.copy()
    invalid.loc[0, "product_category"] = None

    with pytest.raises(ValueError, match="contains missing values"):
        analyze_product_performance(invalid)


def test_summarize_product_concentration(sample_products):
    result = summarize_product_concentration(sample_products)

    assert result["total_products"] == 4
    assert result["products_with_delivered_sales"] == 3
    assert result["products_without_delivered_sales"] == 1

    assert result["catalogue_sales_penetration"] == pytest.approx(75)

    assert result["top_10_revenue_share"] == pytest.approx(100)
    assert result["top_20_revenue_share"] == pytest.approx(100)
    assert result["top_50_revenue_share"] == pytest.approx(100)

    assert result["product_revenue_hhi"] == pytest.approx(4600)

    assert result["products_with_one_seller"] == 1
    assert result["products_with_multiple_sellers"] == 2
    assert result["average_sellers_per_selling_product"] == pytest.approx(2)

    assert result["total_delivered_item_lines"] == 100
    assert result["total_delivered_product_value"] == 10000

    assert result["top_10_products"] == [
        "product_a",
        "product_b",
        "product_c",
    ]


def test_product_concentration_rejects_duplicate_products(sample_products):
    duplicated = pd.concat(
        [sample_products, sample_products.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="one row per product"):
        summarize_product_concentration(duplicated)


def test_product_concentration_rejects_zero_total_revenue(sample_products):
    invalid = sample_products.copy()
    invalid["delivered_product_value"] = 0

    with pytest.raises(ValueError, match="must be positive"):
        summarize_product_concentration(invalid)


def test_product_concentration_rejects_missing_columns(sample_products):
    incomplete = sample_products.drop(columns=["distinct_sellers"])

    with pytest.raises(ValueError, match="Missing required columns"):
        summarize_product_concentration(incomplete)
