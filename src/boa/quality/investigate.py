import pandas as pd

from boa.config.datasets import DATASETS, RAW_DATA_DIR


def load_dataset(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / DATASETS[name])


def investigate_orders() -> None:
    df = load_dataset("orders")

    print("\n========== ORDER STATUS INVESTIGATION ==========")

    date_columns = [
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
    ]

    for column in date_columns:
        print(f"\nMissing {column} by order status:")

        result = (
            df.assign(is_missing=df[column].isna())
            .groupby("order_status")["is_missing"]
            .agg(["sum", "count"])
        )

        result["missing_percentage"] = (result["sum"] / result["count"] * 100).round(2)

        print(result.to_string())


def investigate_products() -> None:
    df = load_dataset("products")

    print("\n========== PRODUCT INVESTIGATION ==========")

    columns = [
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    print("\nMissing-value patterns:")

    patterns = df[columns].isna().value_counts().reset_index(name="row_count")

    print(patterns.to_string(index=False))

    print("\nProducts missing physical measurements:")

    physical_columns = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    print(df[physical_columns].isna().sum())


def investigate_geolocation() -> None:
    df = load_dataset("geolocation")

    print("\n========== GEOLOCATION INVESTIGATION ==========")

    exact_duplicates = df.duplicated().sum()

    print(f"\nExact duplicate rows: {exact_duplicates:,}")

    print("\nUnique postcodes:")
    print(df["geolocation_zip_code_prefix"].nunique())

    print("\nUnique coordinate combinations:")
    print(df[["geolocation_lat", "geolocation_lng"]].drop_duplicates().shape[0])

    print("\nPostcodes with multiple coordinates:")

    coordinates_per_zip = df.groupby("geolocation_zip_code_prefix").apply(
        lambda group: (
            group[["geolocation_lat", "geolocation_lng"]].drop_duplicates().shape[0]
        ),
        include_groups=False,
    )

    print((coordinates_per_zip > 1).sum())

    print("\nCoordinate count distribution:")
    print(coordinates_per_zip.describe())


def main() -> None:
    investigate_orders()
    investigate_products()
    investigate_geolocation()


if __name__ == "__main__":
    main()
