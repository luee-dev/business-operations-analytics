import json
import logging
from pathlib import Path

from boa.config.datasets import RAW_DATA_DIR
from boa.ingestion.profiler import (
    profile_all_datasets,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def main():
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError("Raw data directory does not exist.")

    report = profile_all_datasets()

    output_dir = Path("reports/data_quality")
    output_dir.mkdir(parents=True, exist_ok=True)

    report.to_csv(
        output_dir / "initial_profile.csv",
        index=False,
    )

    readable_report = report[
        [
            "dataset",
            "row_count",
            "column_count",
            "duplicate_rows",
            "missing_values",
        ]
    ]

    print(readable_report.to_string(index=False))

    print("\nProfiling completed successfully.")


if __name__ == "__main__":
    main()
