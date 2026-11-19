
import logging
from pathlib import Path

import pandas as pd

from boa.config.datasets import DATASETS
from boa.quality.rules import DATASET_RULES


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_result(
    dataset: str,
    rule: str,
    status: str,
    affected_rows: int = 0,
    severity: str = "ERROR",
    details: str = "",
    recommendation: str = "",
) -> dict:
    """Create a consistent validation result."""

    return {
        "dataset": dataset,
        "rule": rule,
        "status": status,
        "severity": severity,
        "affected_rows": affected_rows,
        "details": details,
        "recommendation": recommendation,
    }


def validate_dataset(dataset_name: str, filename: str) -> list[dict]:
    """Execute configured and dataset-specific quality checks."""

    file_path = PROCESSED_DATA_DIR / filename
    results = []

    # --------------------------------------------------
    # 0. Check whether the processed file exists
    # --------------------------------------------------

    if not file_path.exists():
        return [
            create_result(
                dataset_name,
                "file_exists",
                "FAILED",
                severity="CRITICAL",
                details=f"Processed file not found: {file_path}",
                recommendation="Run the cleaning pipeline before validation.",
            )
        ]

    logger.info("Validating dataset: %s", dataset_name)

    df = pd.read_csv(file_path)
    rules = DATASET_RULES[dataset_name]

    # --------------------------------------------------
    # 1. Required columns
    # --------------------------------------------------

    missing_columns = [
        column
        for column in rules.required_columns
        if column not in df.columns
    ]

    results.append(
        create_result(
            dataset_name,
            "required_columns",
            "FAILED" if missing_columns else "PASSED",
            affected_rows=len(missing_columns),
            severity="CRITICAL",
            details=(
                f"Missing columns: {missing_columns}"
                if missing_columns
                else "All required columns are present."
            ),
            recommendation=(
                "Investigate the source file or ingestion process."
                if missing_columns
                else ""
            ),
        )
    )

    # Stop checks that depend on missing required columns.
    if missing_columns:
        return results

    # --------------------------------------------------
    # 2. Unique key checks
    # --------------------------------------------------

    for column in rules.unique_columns:
        duplicate_count = int(
            df.duplicated(subset=[column], keep=False).sum()
        )

        results.append(
            create_result(
                dataset_name,
                f"unique_{column}",
                "FAILED" if duplicate_count else "PASSED",
                affected_rows=duplicate_count,
                details=(
                    f"{duplicate_count} rows participate in duplicate keys."
                ),
                recommendation=(
                    "Investigate duplicate records before loading "
                    "the dataset into the analytical layer."
                    if duplicate_count
                    else ""
                ),
            )
        )

    # --------------------------------------------------
    # 2.1 Composite key checks
    # --------------------------------------------------

    if dataset_name == "order_items":
        key_columns = ["order_id", "order_item_id"]

        duplicate_count = int(
            df.duplicated(subset=key_columns, keep=False).sum()
        )

        results.append(
            create_result(
                dataset_name,
                "unique_order_item_key",
                "FAILED" if duplicate_count else "PASSED",
                affected_rows=duplicate_count,
                details=f"Duplicate composite keys: {duplicate_count}",
                recommendation=(
                    "Investigate duplicated order-item records."
                    if duplicate_count
                    else ""
                ),
            )
        )

    # --------------------------------------------------
    # 3. Non-null checks
    # --------------------------------------------------

    for column in rules.non_null_columns:
        missing_count = int(df[column].isna().sum())

        results.append(
            create_result(
                dataset_name,
                f"not_null_{column}",
                "FAILED" if missing_count else "PASSED",
                affected_rows=missing_count,
                details=f"Missing values: {missing_count}",
                recommendation=(
                    "Investigate missing critical identifiers or fields."
                    if missing_count
                    else ""
                ),
            )
        )

    # --------------------------------------------------
    # 4. Financial value checks
    # --------------------------------------------------

    for column in rules.positive_columns:
        zero_count = int((df[column] == 0).sum())
        negative_count = int((df[column] < 0).sum())

        # Negative values are validation failures.
        results.append(
            create_result(
                dataset_name,
                f"non_negative_{column}",
                "FAILED" if negative_count else "PASSED",
                affected_rows=negative_count,
                details=f"Negative values: {negative_count}",
                recommendation=(
                    "Investigate negative financial values."
                    if negative_count
                    else ""
                ),
            )
        )

        # Zero values are warnings, not automatic failures.
        if zero_count:
            results.append(
                create_result(
                    dataset_name,
                    f"zero_{column}",
                    "WARNING",
                    affected_rows=zero_count,
                    severity="WARNING",
                    details=f"Zero-value records: {zero_count}",
                    recommendation=(
                        "Investigate zero-value financial records "
                        "before deciding whether they are legitimate."
                    ),
                )
            )

    # --------------------------------------------------
    # 5. Review score range
    # --------------------------------------------------

    if dataset_name == "reviews":
        invalid_count = int(
            (~df["review_score"].between(1, 5)).sum()
        )

        results.append(
            create_result(
                dataset_name,
                "review_score_range",
                "FAILED" if invalid_count else "PASSED",
                affected_rows=invalid_count,
                details=f"Scores outside the 1-5 range: {invalid_count}",
                recommendation=(
                    "Investigate invalid review scores."
                    if invalid_count
                    else ""
                ),
            )
        )

    # --------------------------------------------------
    # 6. Geolocation coordinate ranges
    # --------------------------------------------------

    if dataset_name == "geolocation":
        coordinate_checks = [
            ("geolocation_lat", -90, 90),
            ("geolocation_lng", -180, 180),
        ]

        for column, lower, upper in coordinate_checks:
            invalid_count = int(
                (~df[column].between(lower, upper)).sum()
            )

            results.append(
                create_result(
                    dataset_name,
                    f"valid_range_{column}",
                    "FAILED" if invalid_count else "PASSED",
                    affected_rows=invalid_count,
                    details=(
                        f"Values outside the range "
                        f"{lower} to {upper}: {invalid_count}"
                    ),
                    recommendation=(
                        "Investigate invalid geographic coordinates."
                        if invalid_count
                        else ""
                    ),
                )
            )

    # --------------------------------------------------
    # 7. Order timestamp sequence
    # --------------------------------------------------

    if dataset_name == "orders":
        date_columns = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
        ]

        for column in date_columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                utc=True,
            )

        timestamp_checks = [
            (
                "purchase_before_approval",
                "order_purchase_timestamp",
                "order_approved_at",
            ),
            (
                "approval_before_carrier_delivery",
                "order_approved_at",
                "order_delivered_carrier_date",
            ),
            (
                "carrier_before_customer_delivery",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
            ),
        ]

        for rule_name, earlier, later in timestamp_checks:
            invalid = (
                df[earlier].notna()
                & df[later].notna()
                & (df[earlier] > df[later])
            )

            invalid_count = int(invalid.sum())

            results.append(
                create_result(
                    dataset_name,
                    rule_name,
                    "FAILED" if invalid_count else "PASSED",
                    affected_rows=invalid_count,
                    details=(
                        f"Timestamp sequence violations: {invalid_count}"
                    ),
                    recommendation=(
                        "Investigate records with inconsistent timestamps. "
                        "Do not automatically reorder timestamps."
                        if invalid_count
                        else ""
                    ),
                )
            )

        # Delivered orders should normally have a delivery timestamp.
        missing_delivery = (
            df["order_status"].eq("delivered")
            & df["order_delivered_customer_date"].isna()
        )

        missing_delivery_count = int(missing_delivery.sum())

        results.append(
            create_result(
                dataset_name,
                "delivered_order_has_delivery_timestamp",
                "WARNING" if missing_delivery_count else "PASSED",
                affected_rows=missing_delivery_count,
                severity="WARNING",
                details=(
                    f"Delivered orders missing delivery timestamps: "
                    f"{missing_delivery_count}"
                ),
                recommendation=(
                    "Investigate these records; do not fabricate timestamps."
                    if missing_delivery_count
                    else ""
                ),
            )
        )

    return results


def main() -> None:
    """Run validation across all configured datasets."""

    all_results = []

    for dataset_name, filename in DATASETS.items():
        results = validate_dataset(dataset_name, filename)
        all_results.extend(results)

    results_df = pd.DataFrame(all_results)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "validation_report.csv"
    results_df.to_csv(report_path, index=False)

    print("\n========== DATA QUALITY VALIDATION ==========")

    if not results_df.empty:
        summary = (
            results_df.groupby(["status", "severity"])
            .size()
            .unstack(fill_value=0)
        )

        print("\nValidation summary:")
        print(summary.to_string())

        print("\nFailed and warning checks:")

        issues = results_df[
            results_df["status"].isin(["FAILED", "WARNING"])
        ]

        if issues.empty:
            print("No failed or warning checks.")
        else:
            print(
                issues[
                    [
                        "dataset",
                        "rule",
                        "status",
                        "severity",
                        "affected_rows",
                        "details",
                        "recommendation",
                    ]
                ].to_string(index=False)
            )

    print(f"\nFull report saved to: {report_path}")


if __name__ == "__main__":
    main()
