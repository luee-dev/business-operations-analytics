
# Product and Category Performance Analysis

## 1. Objective

Evaluate product and category-level commercial performance using
delivered order-item data from the Olist marketplace dataset.

The analysis examines sales value, product assortment, category
contribution, product productivity, cancellation patterns and
catalogue data quality.

## 2. Data and methodology

- Product dimension: 32,951 products.
- Order-item fact: 112,650 records.
- Products with delivered sales: 32,216.
- Delivered orders: 96,478.
- Delivered product value: R$13,221,498.11.
- Delivered freight value: R$2,198,275.64.

Commercial performance is measured using delivered orders.
Canceled and other order statuses are retained separately.

Product-level metrics are aggregated at product grain.
Category metrics are aggregated using translated category labels,
with missing labels assigned to an uncategorized group.

## 3. Category performance

Leading categories by delivered product value:

| Category | Delivered value | Share |
|---|---:|---:|
| Health & beauty | R$1,233,131.72 | 9.33% |
| Watches & gifts | R$1,166,176.98 | 8.82% |
| Bed, bath & table | R$1,023,434.76 | 7.74% |
| Sports & leisure | R$954,852.55 | 7.22% |
| Computers & accessories | R$888,724.61 | 6.72% |

The top five categories account for 39.83% of delivered product value.
The top ten account for approximately 62.43%.

## 4. Product concentration

There are 32,216 products with delivered sales.

| Measure | Share |
|---|---:|
| Top 10 products | 3.35% |
| Top 20 products | 5.45% |
| Top 50 products | 9.38% |

Category-level HHI: 489.42.

These results indicate relatively distributed product and category
sales rather than strong dependence on a small number of products.

## 5. Product productivity

The computers category generated R$7,289.47 in delivered product
value per catalogue product across 30 products.

Health & beauty generated the largest total category value,
R$1,233,131.72, across 2,444 products.

Category productivity should be interpreted alongside catalogue
size and sales volume. Small categories can have high average
values because of limited assortment and higher-priced products.

## 6. Data quality

- 610 products have incomplete product metadata.
- All 610 are grouped under the uncategorized category.
- One product has incomplete physical measurements.
- Product dimension keys and IDs are unique.
- Category-level totals reconcile with product-level totals.

## 7. Business implications

1. Health & beauty and watches & gifts are major commercial
   categories worth monitoring.
2. The top five categories contribute a substantial but not
   dominant share of delivered product value.
3. The computers category warrants further investigation because
   of its high delivered value per catalogue product.
4. Product sales are broadly distributed, reducing apparent
   dependence on a small number of individual products.
5. Missing category metadata should be investigated to improve
   catalogue classification and reporting.

## 8. Limitations

Delivered product value is not profit or contribution margin.
Product costs, commissions, advertising expenses and operating
costs are unavailable in this analysis.

The dataset is historical. Results describe the observed
marketplace period and should not be interpreted as current
market performance.
