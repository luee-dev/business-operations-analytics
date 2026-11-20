from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from boa.reporting.data import build_report_data

OUTPUT_PATH = Path("reports/automated/business_operations_performance_report.pdf")


def format_number(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"R$ {value:,.2f}"


def format_percentage(value, already_percent=False):
    if pd.isna(value):
        return "N/A"

    percentage = value if already_percent else value * 100
    return f"{percentage:.2f}%"


def format_cell(value):
    if pd.isna(value):
        return "N/A"

    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return f"{value:,.0f}"

        return format_number(value)

    return str(value)


def make_table(data, widths=None):
    table = Table(data, colWidths=widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F0F4F8"),
                    ],
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return table


def dataframe_table(df, columns, limit=10, formatters=None):
    available = [column for column in columns if column in df.columns]

    if not available:
        return None

    formatters = formatters or {}

    rows = [available]

    for _, record in df[available].head(limit).iterrows():
        rows.append(
            [
                formatters.get(column, format_cell)(record[column])
                for column in available
            ]
        )

    return make_table(rows)


def add_page_number(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#52606D"))
    canvas.drawString(15 * mm, 10 * mm, "Business Operations & Performance Report")
    canvas.drawRightString(
        landscape(A4)[0] - 15 * mm,
        10 * mm,
        f"Page {document.page}",
    )
    canvas.restoreState()


def generate_business_performance_report(output_path=OUTPUT_PATH):
    report = build_report_data()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_size = landscape(A4)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=page_size,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title="Business Operations & Performance Report",
        author="Business Operations Analytics Platform",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#243B53"),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#243B53"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )

    story = []

    # Cover and executive summary.
    story.append(
        Paragraph(
            "Business Operations &amp; Performance Report",
            styles["ReportTitle"],
        )
    )
    story.append(
        Paragraph(
            f"Generated: {datetime.now().astimezone():%d %B %Y, %H:%M %Z}",
            styles["ReportBody"],
        )
    )
    story.append(Spacer(1, 8))

    delivery = report["delivery_summary"]
    experience = report["customer_experience"]

    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))

    executive_metrics = [
        ["Metric", "Result", "Metric", "Result"],
        [
            "Total orders",
            f"{delivery['total_orders']:,}",
            "Delivered orders",
            f"{delivery['delivered_orders']:,}",
        ],
        [
            "Eligible delivery orders",
            f"{delivery['eligible_orders']:,}",
            "Late delivery rate",
            format_percentage(delivery["late_delivery_rate"], True),
        ],
        [
            "Average delivery time",
            f"{format_number(delivery['average_delivery_days'])} days",
            "Customer experience eligible orders",
            f"{experience['eligible_orders']:,}",
        ],
    ]

    story.append(make_table(executive_metrics))
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "This report summarizes historical marketplace operations. "
            "The findings describe the observed dataset and should not be "
            "interpreted as current market performance or causal evidence.",
            styles["ReportBody"],
        )
    )

    story.append(PageBreak())

    # Delivery performance.
    story.append(Paragraph("1. Delivery Performance", styles["SectionHeading"]))

    delivery_rows = [
        ["Metric", "Value"],
        ["Delivered orders", f"{delivery['delivered_orders']:,}"],
        ["Eligible orders", f"{delivery['eligible_orders']:,}"],
        ["Late orders", f"{delivery['late_orders']:,}"],
        [
            "Late delivery rate",
            format_percentage(delivery["late_delivery_rate"], True),
        ],
        [
            "On-time delivery rate",
            format_percentage(delivery["on_time_delivery_rate"], True),
        ],
        [
            "Average delivery duration",
            f"{format_number(delivery['average_delivery_days'])} days",
        ],
        [
            "Median delivery duration",
            f"{format_number(delivery['median_delivery_days'])} days",
        ],
        [
            "90th percentile delivery duration",
            f"{format_number(delivery['p90_delivery_days'])} days",
        ],
        [
            "Delivered orders missing timestamps",
            f"{delivery['delivered_missing_timestamps']:,}",
        ],
    ]

    story.append(make_table(delivery_rows))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Monthly Delivery Performance", styles["Heading3"]))

    monthly = report["monthly_delivery"]
    monthly_table = dataframe_table(
        monthly,
        [
            "purchase_month",
            "eligible_orders",
            "late_orders",
            "late_delivery_rate",
            "rolling_3m_late_delivery_rate",
        ],
        limit=26,
        formatters={
            "late_delivery_rate": lambda value: format_percentage(value, True),
            "rolling_3m_late_delivery_rate": lambda value: format_percentage(
                value, True
            ),
        },
    )

    if monthly_table:
        story.append(monthly_table)

    # Customer analytics.
    story.append(PageBreak())
    story.append(Paragraph("2. Customer Analytics", styles["SectionHeading"]))

    story.append(Paragraph("Customer Segments", styles["Heading3"]))

    segment_table = dataframe_table(
        report["customer_segments"],
        [
            "customer_segment",
            "customer_count",
            "total_orders",
            "total_customer_value",
            "avg_customer_value",
        ],
        limit=20,
        formatters={
            "total_customer_value": format_currency,
            "avg_customer_value": format_currency,
        },
    )

    if segment_table:
        story.append(segment_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("Repeat Purchase Behaviour", styles["Heading3"]))

    repeat_table = dataframe_table(
        report["repeat_purchase"],
        [
            "purchase_group",
            "customer_count",
            "delivered_orders",
            "total_customer_value",
            "avg_order_value",
        ],
        limit=10,
        formatters={
            "total_customer_value": format_currency,
            "avg_order_value": format_currency,
        },
    )

    if repeat_table:
        story.append(repeat_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("Customer Recency", styles["Heading3"]))

    recency_table = dataframe_table(
        report["customer_recency"],
        [
            "recency_group",
            "customer_count",
            "total_customer_value",
            "median_recency_days",
        ],
        limit=10,
        formatters={
            "total_customer_value": format_currency,
        },
    )

    if recency_table:
        story.append(recency_table)

    # Product and category performance.
    # story.append(PageBreak())
    story.append(
        Paragraph("3. Product &amp; Category Performance", styles["SectionHeading"])
    )

    category_concentration = report["category_concentration"]

    concentration_rows = [
        ["Category concentration metric", "Value"],
        [
            "Top 5 category revenue share",
            format_percentage(category_concentration["top_5_revenue_share"], True),
        ],
        [
            "Top 10 category revenue share",
            format_percentage(category_concentration["top_10_revenue_share"], True),
        ],
        [
            "Category HHI",
            format_number(category_concentration["category_hhi"]),
        ],
    ]

    story.append(make_table(concentration_rows))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Leading Categories", styles["Heading3"]))

    category_table = dataframe_table(
        report["category_performance"],
        [
            "product_category",
            "total_products",
            "delivered_item_lines",
            "delivered_product_value",
            "revenue_share",
        ],
        limit=10,
        formatters={
            "delivered_product_value": format_currency,
            "revenue_share": lambda value: format_percentage(value, True),
        },
    )

    if category_table:
        story.append(category_table)

    story.append(Spacer(1, 10))

    product_concentration = report["product_concentration"]

    product_rows = [
        ["Product concentration metric", "Value"],
        [
            "Products with delivered sales",
            f"{product_concentration['products_with_delivered_sales']:,}",
        ],
        [
            "Products without delivered sales",
            f"{product_concentration['products_without_delivered_sales']:,}",
        ],
        [
            "Top 10 product revenue share",
            format_percentage(product_concentration["top_10_revenue_share"], True),
        ],
        [
            "Top 50 product revenue share",
            format_percentage(product_concentration["top_50_revenue_share"], True),
        ],
    ]

    story.append(make_table(product_rows))

    # Seller performance.
    # story.append(PageBreak())
    story.append(Paragraph("4. Seller Performance", styles["SectionHeading"]))

    seller_concentration = report["seller_concentration"]

    seller_rows = [
        ["Seller concentration metric", "Value"],
        ["Total sellers", f"{seller_concentration['total_sellers']:,}"],
        [
            "Sellers with delivered sales",
            f"{seller_concentration['sellers_with_delivered_sales']:,}",
        ],
        [
            "Top 10 seller revenue share",
            format_percentage(seller_concentration["top_10_revenue_share"], True),
        ],
        [
            "Top 20 seller revenue share",
            format_percentage(seller_concentration["top_20_revenue_share"], True),
        ],
    ]

    story.append(make_table(seller_rows))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Elevated Operational Risk Screening", styles["Heading3"]))

    risk = report["seller_operational_risk"]
    elevated = risk[risk["operational_risk"] == "Elevated"].copy()

    risk_table = dataframe_table(
        elevated.sort_values(
            "excess_late_associations",
            ascending=False,
        ),
        [
            "seller_id",
            "delivery_estimate_eligible_orders",
            "late_delivery_rate",
            "excess_late_associations",
            "operational_risk",
        ],
        limit=15,
        formatters={
            "late_delivery_rate": lambda value: format_percentage(value, True),
        },
    )

    if risk_table:
        story.append(risk_table)

    story.append(
        Paragraph(
            f"The screening identified {len(elevated):,} elevated-risk sellers "
            f"among {len(risk):,} sellers meeting the eligibility threshold. "
            "This is a statistical screening result, not proof of seller "
            "fault or confirmed operational failure. Multiple testing may "
            "increase false-positive findings.",
            styles["ReportBody"],
        )
    )

    # Customer experience.
    story.append(PageBreak())
    story.append(Paragraph("5. Customer Experience", styles["SectionHeading"]))

    late = experience["late"]
    on_time = experience["on_time"]

    experience_rows = [
        ["Metric", "Late delivery", "On-time delivery"],
        [
            "Eligible orders",
            f"{late['orders']:,}",
            f"{on_time['orders']:,}",
        ],
        [
            "Average review score",
            format_number(late["average_review_score"]),
            format_number(on_time["average_review_score"]),
        ],
        [
            "Median review score",
            format_number(late["median_review_score"]),
            format_number(on_time["median_review_score"]),
        ],
        [
            "Negative review order rate",
            format_percentage(late["negative_review_order_rate"]),
            format_percentage(on_time["negative_review_order_rate"]),
        ],
        [
            "Average delivery duration",
            f"{format_number(late['average_delivery_days'])} days",
            f"{format_number(on_time['average_delivery_days'])} days",
        ],
    ]

    story.append(make_table(experience_rows))
    story.append(Spacer(1, 10))

    differences = experience["differences"]
    tests = experience["statistical_tests"]

    story.append(Paragraph("Observed Differences", styles["Heading3"]))

    difference_rows = [
        ["Measure", "Late minus on-time"],
        [
            "Average review score difference",
            format_number(differences["average_review_score"]),
        ],
        [
            "Negative review order rate difference",
            format_percentage(differences["negative_review_order_rate"]),
        ],
    ]

    story.append(make_table(difference_rows))
    story.append(Spacer(1, 10))

    test_rows = [["Statistical test", "p-value"]]

    for test_name, result in tests.items():
        test_rows.append(
            [
                test_name.replace("_", " "),
                format_number(result["p_value"], 6),
            ]
        )

    story.append(make_table(test_rows))
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "The observed differences indicate an association between "
            "delivery timeliness and customer review outcomes. They do not "
            "establish that delivery delays alone caused lower review scores. "
            "Very small p-values should be interpreted alongside effect sizes "
            "and the large sample size.",
            styles["ReportBody"],
        )
    )

    # Build PDF.
    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return output_path
