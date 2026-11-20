import pytest
from pypdf import PdfReader

from boa.reporting.pdf import (
    OUTPUT_PATH,
    format_cell,
    format_currency,
    format_number,
    format_percentage,
    generate_business_performance_report,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1000, "1,000.00"),
        (1234.567, "1,234.57"),
        (0, "0.00"),
    ],
)
def test_format_number(value, expected):
    assert format_number(value) == expected


def test_format_number_handles_missing_values():
    assert format_number(float("nan")) == "N/A"


def test_format_currency():
    assert format_currency(1250) == "R$ 1,250.00"


def test_format_percentage():
    assert format_percentage(0.25) == "25.00%"


def test_format_cell_formats_integer_without_decimals():
    assert format_cell(99441) == "99,441"


def test_format_cell_formats_decimal_to_two_places():
    assert format_cell(12.5582) == "12.56"


def test_format_cell_handles_missing_values():
    assert format_cell(float("nan")) == "N/A"


def test_format_cell_preserves_text():
    assert format_cell("delivered") == "delivered"


def test_generate_business_performance_report(tmp_path):
    output_path = tmp_path / "test_report.pdf"

    result = generate_business_performance_report(output_path)

    assert result.exists()
    assert result.stat().st_size > 0

    reader = PdfReader(result)

    assert len(reader.pages) >= 5
    assert reader.metadata.title == "Business Operations & Performance Report"


def test_generated_report_contains_required_sections():
    assert OUTPUT_PATH.exists()

    reader = PdfReader(OUTPUT_PATH)
    report_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    required_sections = [
        "Executive Summary",
        "Delivery Performance",
        "Customer Analytics",
        "Product",
        "Seller Performance",
        "Customer Experience",
    ]

    for section in required_sections:
        assert section.lower() in report_text.lower(), (
            f"Missing report section: {section}"
        )
