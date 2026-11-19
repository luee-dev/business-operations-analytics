import pandas as pd


def analyze_category_performance(
    categories: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyse category sales contribution, catalogue productivity
    and order cancellation rates.
    """
    required_columns = {
        "product_category",
        "total_products",
        "total_order_item_lines",
        "total_orders",
        "delivered_item_lines",
        "delivered_orders",
        "canceled_orders",
        "delivered_product_value",
        "average_delivered_item_price",
    }

    missing_columns = required_columns.difference(categories.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if categories["product_category"].duplicated().any():
        raise ValueError("Expected one row per product category.")

    if categories[list(required_columns)].isna().any().any():
        raise ValueError("Category data contains missing values.")

    summary = categories[
        [
            "product_category",
            "total_products",
            "total_order_item_lines",
            "total_orders",
            "delivered_item_lines",
            "delivered_orders",
            "canceled_orders",
            "delivered_product_value",
            "average_delivered_item_price",
        ]
    ].copy()

    total_delivered_value = summary["delivered_product_value"].sum()

    summary["revenue_share"] = (
        summary["delivered_product_value"]
        / total_delivered_value
        * 100
    )

    summary["revenue_per_catalogue_product"] = (
        summary["delivered_product_value"]
        / summary["total_products"].replace(0, pd.NA)
    )

    summary["cancellation_rate"] = (
        summary["canceled_orders"]
        / summary["total_orders"].replace(0, pd.NA)
        * 100
    )

    return summary.sort_values(
        "delivered_product_value",
        ascending=False,
    ).reset_index(drop=True)



def analyze_category_concentration(
    categories: pd.DataFrame,
) -> dict:
    """
    Measure delivered-sales concentration and category
    productivity relative to catalogue size.
    """
    analysis = analyze_category_performance(categories)

    total_products = analysis["total_products"].sum()

    analysis["catalogue_share"] = (
        analysis["total_products"] / total_products * 100
    )

    analysis["productivity_index"] = (
        analysis["revenue_share"] / analysis["catalogue_share"]
    )

    # HHI uses percentage shares, producing a score from
    # close to zero to 10,000.
    hhi = (analysis["revenue_share"] ** 2).sum()

    return {
        "top_5_revenue_share": analysis.head(5)["revenue_share"].sum(),
        "top_10_revenue_share": analysis.head(10)["revenue_share"].sum(),
        "category_hhi": hhi,
        "top_categories": analysis.head(10),
        "highest_productivity": analysis.nlargest(
            10, "productivity_index"
        ),
        "lowest_productivity": analysis.nsmallest(
            10, "productivity_index"
        ),
    }


def analyze_product_performance(
    products: pd.DataFrame,
) -> pd.DataFrame:
    """
    Rank products by delivered revenue and calculate
    their revenue contribution and cumulative concentration.
    """
    required_columns = {
        "product_id",
        "product_category",
        "total_orders",
        "distinct_sellers",
        "delivered_item_lines",
        "delivered_product_value",
        "average_delivered_item_price",
    }

    missing_columns = required_columns.difference(products.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if products["product_id"].duplicated().any():
        raise ValueError("Expected one row per product.")

    if products[list(required_columns)].isna().any().any():
        raise ValueError("Product data contains missing values.")

    if (products["delivered_product_value"] < 0).any():
        raise ValueError("Delivered product value cannot be negative.")

    result = products.copy()

    total_revenue = result["delivered_product_value"].sum()

    if total_revenue <= 0:
        raise ValueError("Total delivered revenue must be positive.")

    result["revenue_share"] = (
        result["delivered_product_value"] / total_revenue * 100
    )

    result = result.sort_values(
        "delivered_product_value",
        ascending=False,
    ).reset_index(drop=True)

    result["revenue_rank"] = range(1, len(result) + 1)

    result["cumulative_revenue_share"] = (
        result["revenue_share"].cumsum()
    )

    return result


def summarize_product_concentration(
    products: pd.DataFrame,
) -> dict:
    """
    Calculate catalogue activity, product revenue concentration
    and seller coverage.
    """
    required_columns = {
        "product_id",
        "distinct_sellers",
        "delivered_item_lines",
        "delivered_product_value",
    }

    missing_columns = required_columns.difference(products.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if products["product_id"].duplicated().any():
        raise ValueError("Expected one row per product.")

    selling_products = products.loc[
        products["delivered_product_value"] > 0
    ].copy()

    total_products = len(products)
    active_products = len(selling_products)
    total_revenue = products["delivered_product_value"].sum()

    if total_revenue <= 0:
        raise ValueError("Total delivered revenue must be positive.")

    shares = (
        selling_products["delivered_product_value"]
        / total_revenue
        * 100
    )

    ranked = selling_products.sort_values(
        "delivered_product_value",
        ascending=False,
    )

    seller_coverage = selling_products["distinct_sellers"]

    return {
        "total_products": total_products,
        "products_with_delivered_sales": active_products,
        "products_without_delivered_sales": (
            total_products - active_products
        ),
        "catalogue_sales_penetration": (
            active_products / total_products * 100
        ),
        "top_10_revenue_share": shares.nlargest(10).sum(),
        "top_20_revenue_share": shares.nlargest(20).sum(),
        "top_50_revenue_share": shares.nlargest(50).sum(),
        "product_revenue_hhi": (shares ** 2).sum(),
        "products_with_one_seller": (
            seller_coverage == 1
        ).sum(),
        "products_with_multiple_sellers": (
            seller_coverage > 1
        ).sum(),
        "average_sellers_per_selling_product": (
            seller_coverage.mean()
        ),
        "total_delivered_item_lines": (
            products["delivered_item_lines"].sum()
        ),
        "total_delivered_product_value": total_revenue,
        "top_10_products": ranked.head(10)["product_id"].tolist(),
    }