
import pandas as pd

DATA_DIR = "data/processed"

payments = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset.csv")
orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv")
items = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv")

# Select zero-value payments
zero_payments = payments[payments["payment_value"] == 0].copy()

# Aggregate item values by order
order_totals = (
    items.groupby("order_id")
    .agg(
        item_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
        item_count=("order_item_id", "count"),
    )
    .reset_index()
)

# Aggregate payment values by order
payment_totals = (
    payments.groupby("order_id")
    .agg(
        total_payment=("payment_value", "sum"),
        payment_count=("payment_value", "count"),
    )
    .reset_index()
)

# Attach order status
result = (
    zero_payments
    .merge(
        orders[["order_id", "order_status"]],
        on="order_id",
        how="left",
    )
    .merge(order_totals, on="order_id", how="left")
    .merge(payment_totals, on="order_id", how="left")
)

print(f"Zero-value payment records: {len(result)}")
print("\nZERO-VALUE PAYMENT DETAILS")

columns = [
    "order_id",
    "payment_sequential",
    "payment_type",
    "payment_value",
    "order_status",
    "item_total",
    "freight_total",
    "item_count",
    "total_payment",
    "payment_count",
]

print(result[columns].to_string(index=False))

print("\nZERO-VALUE RECORDS BY PAYMENT TYPE")
print(result["payment_type"].value_counts(dropna=False))

print("\nZERO-VALUE RECORDS BY ORDER STATUS")
print(result["order_status"].value_counts(dropna=False))

print("\nZERO-VALUE RECORDS WITH NO ORDER ITEMS")
print(result[result["item_count"].isna()][columns].to_string(index=False))
