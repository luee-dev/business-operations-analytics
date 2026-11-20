import pandas as pd
from sqlalchemy import text

from boa.config.database import get_engine

# Only allow access to known, validated analytics views.
ANALYTICS_VIEWS = {
    "vw_order_performance",
    "vw_customer_performance",
    "vw_customer_rfm",
    "vw_product_performance",
    "vw_category_performance",
    "vw_seller_performance",
    "vw_delivery_review_analysis",
    "vw_order_review_performance",
    "vw_category_review_analysis",
    "vw_payment_delivery_analysis",
    "vw_customer_segment_category_analysis",
}


def load_analytics_view(view_name: str) -> pd.DataFrame:
    """
    Load a validated analytics view from PostgreSQL into a DataFrame.
    """
    if view_name not in ANALYTICS_VIEWS:
        raise ValueError(f"Unsupported analytics view: {view_name}")

    query = text(f"SELECT * FROM analytics.{view_name}")

    with get_engine().connect() as connection:
        return pd.read_sql_query(query, connection)


def load_order_performance() -> pd.DataFrame:
    return load_analytics_view("vw_order_performance")


def load_customer_rfm() -> pd.DataFrame:
    return load_analytics_view("vw_customer_rfm")


def load_category_performance() -> pd.DataFrame:
    return load_analytics_view("vw_category_performance")


def load_delivery_review_analysis() -> pd.DataFrame:
    return load_analytics_view("vw_delivery_review_analysis")


def load_customer_order_activity() -> pd.DataFrame:
    """
    Load delivered orders with their stable customer identifiers
    for acquisition cohort and retention analysis.
    """
    query = text("""
        SELECT
            dc.customer_unique_id,
            fo.order_id,
            fo.order_purchase_timestamp
        FROM analytics.fact_orders AS fo
        INNER JOIN analytics.dim_customers AS dc
            ON fo.customer_key = dc.customer_key
        WHERE fo.order_status = 'delivered'
    """)

    with get_engine().connect() as connection:
        return pd.read_sql_query(query, connection)
