import logging

import pandas as pd

from boa.config.datasets import DATASETS, RAW_DATA_DIR


logger = logging.getLogger(__name__)


def profile_dataset(dataset_name: str, filename: str) -> dict:
    file_path = RAW_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    profile = {
        "dataset": dataset_name,
        "filename": filename,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": int(df.isna().sum().sum()),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }

    return profile


def profile_all_datasets() -> pd.DataFrame:
    profiles = []

    for dataset_name, filename in DATASETS.items():
        logger.info("Profiling dataset: %s", dataset_name)

        profile = profile_dataset(
            dataset_name,
            filename,
        )

        profiles.append(profile)

    return pd.DataFrame(profiles)
