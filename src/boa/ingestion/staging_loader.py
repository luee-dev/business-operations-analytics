import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from boa.config.database import engine
from boa.config.datasets import DATASETS, PROCESSED_DATA_DIR

# Expected headers in the processed CSV files.
SOURCE_COLUMNS = {
    "customers": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "geolocation": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    "order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "payments": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "reviews": [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "flag_approval_after_carrier",
        "flag_carrier_after_customer_delivery",
        "flag_delivered_missing_timestamp",
        "is_delivered_timestamp_missing",
    ],
    "products": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "is_product_metadata_incomplete",
        "is_physical_measurement_incomplete",
    ],
    "sellers": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "category_translation": [
        "product_category_name",
        "product_category_name_english",
    ],
}


# Columns actually inserted into each staging table.
# The duplicate orders flag is intentionally excluded.
STAGING_COLUMNS = {
    dataset: columns.copy() for dataset, columns in SOURCE_COLUMNS.items()
}

INTEGER_COLUMNS = {
    "customers": [
        "customer_zip_code_prefix",
    ],
    "geolocation": [
        "geolocation_zip_code_prefix",
    ],
    "order_items": [
        "order_item_id",
    ],
    "payments": [
        "payment_sequential",
        "payment_installments",
    ],
    "reviews": [
        "review_score",
    ],
    "products": [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
    ],
    "sellers": [
        "seller_zip_code_prefix",
    ],
    "orders": [],
    "category_translation": [],
}

STAGING_COLUMNS["orders"].remove("is_delivered_timestamp_missing")


def normalize_integer_value(value, dataset_name, column_name):
    """Convert integer-like CSV values such as 40.0 to 40."""

    if value is None or value.strip() == "":
        return None

    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid integer value in {dataset_name}.{column_name}: {value!r}"
        ) from exc

    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(
            f"Non-integer value in {dataset_name}.{column_name}: {value!r}"
        )

    return str(int(number))


def validate_csv_headers(
    file_path: Path,
    expected_columns: list[str],
) -> None:
    """Validate the processed CSV structure."""

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)
        actual_columns = next(reader, [])

    if actual_columns != expected_columns:
        raise ValueError(
            f"Unexpected columns in {file_path.name}.\n"
            f"Expected: {expected_columns}\n"
            f"Actual: {actual_columns}"
        )


def get_source_row_count(file_path: Path) -> int:
    """Count CSV records without loading the whole file into memory."""

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)
        next(reader, None)
        return sum(1 for _ in reader)


def load_csv_to_staging(
    cursor,
    file_path: Path,
    dataset_name: str,
) -> None:
    """Stream processed CSV records into a typed staging table."""

    columns = STAGING_COLUMNS[dataset_name]

    column_sql = ", ".join(f'"{column}"' for column in columns)

    copy_sql = f"COPY staging.{dataset_name} ({column_sql}) FROM STDIN"

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        with cursor.copy(copy_sql) as copy:
            for row in reader:
                values = []

                for column in columns:
                    value = row[column]

                    if value == "":
                        value = None

                    elif column in INTEGER_COLUMNS[dataset_name]:
                        value = normalize_integer_value(
                            value,
                            dataset_name,
                            column,
                        )

                    values.append(value)

                copy.write_row(values)


def load_staging_data() -> list[dict]:
    """Refresh all staging tables in one transaction."""

    results = []

    # Validate every input file before modifying staging.
    for dataset_name, filename in DATASETS.items():
        file_path = PROCESSED_DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Processed dataset not found: {file_path}")

        validate_csv_headers(
            file_path,
            SOURCE_COLUMNS[dataset_name],
        )

    connection = engine.raw_connection()

    try:
        cursor = connection.cursor()

        try:
            table_names = ", ".join(f"staging.{name}" for name in DATASETS)

            cursor.execute(f"TRUNCATE TABLE {table_names} RESTART IDENTITY")

            for dataset_name, filename in DATASETS.items():
                file_path = PROCESSED_DATA_DIR / filename

                source_count = get_source_row_count(file_path)

                load_csv_to_staging(
                    cursor,
                    file_path,
                    dataset_name,
                )

                cursor.execute(f"SELECT COUNT(*) FROM staging.{dataset_name}")

                database_count = cursor.fetchone()[0]

                result = {
                    "dataset": dataset_name,
                    "source_rows": source_count,
                    "database_rows": database_count,
                    "status": (
                        "PASSED" if source_count == database_count else "FAILED"
                    ),
                }

                results.append(result)

                if source_count != database_count:
                    raise ValueError(
                        f"Row count mismatch for {dataset_name}: "
                        f"source={source_count}, "
                        f"database={database_count}"
                    )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()

    finally:
        connection.close()

    return results


def main() -> None:
    print("Starting staging data ingestion...\n")

    results = load_staging_data()

    print(f"{'DATASET':<22}{'SOURCE ROWS':>15}{'DATABASE ROWS':>17}{'STATUS':>12}")
    print("-" * 66)

    for result in results:
        print(
            f"{result['dataset']:<22}"
            f"{result['source_rows']:>15,}"
            f"{result['database_rows']:>17,}"
            f"{result['status']:>12}"
        )

    print("\nStaging ingestion completed successfully.")


if __name__ == "__main__":
    main()
