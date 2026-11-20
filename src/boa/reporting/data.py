from boa.analytics.customer_experience import analyze_customer_experience
from boa.analytics.customers import (
    analyze_customer_recency,
    analyze_customer_segments,
    analyze_repeat_purchase_behavior,
)
from boa.analytics.data_loader import (
    load_analytics_view,
    load_category_performance,
    load_customer_rfm,
    load_order_performance,
)
from boa.analytics.delivery import (
    analyze_delivery_performance,
    analyze_monthly_delivery_performance,
)
from boa.analytics.products import (
    analyze_category_concentration,
    analyze_category_performance,
    analyze_product_performance,
    summarize_product_concentration,
)
from boa.analytics.sellers import (
    analyze_seller_operational_risk,
    analyze_seller_performance,
    summarize_seller_concentration,
)


def build_report_data() -> dict:
    """
    Load validated analytics views and prepare reusable
    business performance metrics for automated reporting.
    """

    # Load source datasets.
    orders = load_order_performance()
    customers = load_customer_rfm()
    categories = load_category_performance()
    products = load_analytics_view("vw_product_performance")
    sellers = load_analytics_view("vw_seller_performance")
    customer_experience_orders = load_analytics_view("vw_order_review_performance")

    # Delivery analysis.
    delivery_summary = analyze_delivery_performance(orders)
    monthly_delivery = analyze_monthly_delivery_performance(orders)

    # Customer analysis.
    customer_segments = analyze_customer_segments(customers)
    repeat_purchase = analyze_repeat_purchase_behavior(customers)
    customer_recency = analyze_customer_recency(customers)

    # Product and category analysis.
    category_analysis = analyze_category_performance(categories)
    category_concentration = analyze_category_concentration(category_analysis)

    product_analysis = analyze_product_performance(products)
    product_concentration = summarize_product_concentration(product_analysis)

    # Seller analysis.
    seller_analysis = analyze_seller_performance(sellers)
    seller_concentration = summarize_seller_concentration(seller_analysis)
    seller_operational_risk = analyze_seller_operational_risk(sellers)

    # Customer experience analysis.
    customer_experience = analyze_customer_experience(customer_experience_orders)

    return {
        "delivery_summary": delivery_summary,
        "monthly_delivery": monthly_delivery,
        "customer_segments": customer_segments,
        "repeat_purchase": repeat_purchase,
        "customer_recency": customer_recency,
        "category_performance": category_analysis,
        "category_concentration": category_concentration,
        "product_performance": product_analysis,
        "product_concentration": product_concentration,
        "seller_performance": seller_analysis,
        "seller_concentration": seller_concentration,
        "seller_operational_risk": seller_operational_risk,
        "customer_experience": customer_experience,
    }
