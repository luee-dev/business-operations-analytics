"""
Central registry of data quality rules.

These rules define expected data properties.
They do not modify the source datasets.
"""

from dataclasses import dataclass, field


@dataclass
class DatasetRules:
    """Quality expectations for an individual dataset."""

    required_columns: list[str] = field(default_factory=list)
    unique_columns: list[str] = field(default_factory=list)
    non_null_columns: list[str] = field(default_factory=list)
    positive_columns: list[str] = field(default_factory=list)


DATASET_RULES = {
    "customers": DatasetRules(
        required_columns=[
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        unique_columns=["customer_id"],
        non_null_columns=["customer_id", "customer_unique_id"],
    ),
    "orders": DatasetRules(
        required_columns=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
        unique_columns=["order_id"],
        non_null_columns=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
    ),
    "order_items": DatasetRules(
        required_columns=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ],
        unique_columns=[],
        non_null_columns=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
        ],
        positive_columns=["price"],
    ),
    "payments": DatasetRules(
        required_columns=[
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        non_null_columns=["order_id", "payment_sequential"],
        positive_columns=["payment_value"],
    ),
    "reviews": DatasetRules(
        required_columns=[
            "review_id",
            "order_id",
            "review_score",
        ],
        non_null_columns=[
            "review_id",
            "order_id",
            "review_score",
        ],
    ),
    "products": DatasetRules(
        required_columns=[
            "product_id",
        ],
        unique_columns=["product_id"],
        non_null_columns=["product_id"],
    ),
    "sellers": DatasetRules(
        required_columns=[
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
        unique_columns=["seller_id"],
        non_null_columns=["seller_id"],
    ),
    "geolocation": DatasetRules(
        required_columns=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
        non_null_columns=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
    ),
    "category_translation": DatasetRules(
        required_columns=[
            "product_category_name",
            "product_category_name_english",
        ],
        unique_columns=["product_category_name"],
        non_null_columns=[
            "product_category_name",
            "product_category_name_english",
        ],
    ),
}
