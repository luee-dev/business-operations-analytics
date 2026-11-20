import logging
from pathlib import Path

import pandas as pd

from boa.config.datasets import DATASETS, RAW_DATA_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def clean_dataset(dataset_name: str, filename: str) -> dict:
    """Clean one dataset and return a summary of transformations."""

    source_path = RAW_DATA_DIR / filename
    output_path = PROCESSED_DATA_DIR / filename

    logger.info("Cleaning dataset: %s", dataset_name)

    df = pd.read_csv(source_path)

    original_rows = len(df)
    original_missing = int(df.isna().sum().sum())

    duplicates_removed = 0
    invalid_dates = 0

    # Remove exact duplicate geolocation records only.
    if dataset_name == "geolocation":
        duplicates_removed = int(df.duplicated().sum())
        df = df.drop_duplicates().copy()

    # Convert known timestamp columns.
    for column in DATE_COLUMNS.get(dataset_name, []):
        if column in df.columns:
            original_non_null = int(df[column].notna().sum())

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                utc=True,
            )

            invalid_dates += original_non_null - int(df[column].notna().sum())

        if dataset_name == "orders":
            # Flag approval timestamps occurring after carrier handover
            df["flag_approval_after_carrier"] = (
                df["order_approved_at"].notna()
                & df["order_delivered_carrier_date"].notna()
                & (df["order_approved_at"] > df["order_delivered_carrier_date"])
            )

            # Flag carrier handover occurring after customer delivery
            df["flag_carrier_after_customer_delivery"] = (
                df["order_delivered_carrier_date"].notna()
                & df["order_delivered_customer_date"].notna()
                & (
                    df["order_delivered_carrier_date"]
                    > df["order_delivered_customer_date"]
                )
            )

            # Flag delivered orders missing customer delivery timestamps
            df["flag_delivered_missing_timestamp"] = (
                df["order_status"] == "delivered"
            ) & df["order_delivered_customer_date"].isna()

    # Flag incomplete product metadata.
    if dataset_name == "products":
        metadata_columns = [
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
        ]

        measurement_columns = [
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]

        df["is_product_metadata_incomplete"] = df[metadata_columns].isna().any(axis=1)

        df["is_physical_measurement_incomplete"] = (
            df[measurement_columns].isna().any(axis=1)
        )

    # Flag delivered orders with missing delivery timestamps.
    if dataset_name == "orders":
        df["is_delivered_timestamp_missing"] = (
            df["order_status"].eq("delivered")
            & df["order_delivered_customer_date"].isna()
        )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    cleaned_missing = int(df.isna().sum().sum())

    summary = {
        "dataset": dataset_name,
        "original_rows": original_rows,
        "cleaned_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "original_missing_values": original_missing,
        "cleaned_missing_values": cleaned_missing,
        "invalid_dates": invalid_dates,
    }

    logger.info(
        "Completed %s: %s -> %s rows",
        dataset_name,
        original_rows,
        len(df),
    )

    return summary


def main() -> None:
    summaries = []

    for dataset_name, filename in DATASETS.items():
        summary = clean_dataset(dataset_name, filename)
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "cleaning_summary.csv"
    summary_df.to_csv(report_path, index=False)

    print("\n========== CLEANING SUMMARY ==========")
    print(summary_df.to_string(index=False))

    print(f"\nCleaning report saved to: {report_path}")
    print(f"Processed datasets saved to: {PROCESSED_DATA_DIR}")


if __name__ == "__main__":
    main()
