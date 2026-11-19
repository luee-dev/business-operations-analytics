
# Data Quality Investigation Findings

## 1. Overview

The Olist dataset was profiled, cleaned and validated before
being prepared for analytical database loading.

The cleaning process preserves legitimate missing values,
original timestamps and financial records. Exact duplicate
geolocation records were removed.

## 2. Payment anomalies

Nine zero-value payment records were identified.

- Six are voucher records associated with orders having
  positive aggregate payment values.
- Three are `not_defined` records associated with canceled
  orders that have no order items and zero aggregate payments.
- The nine records belong to eight distinct orders because
  one order contains two zero-value voucher entries.

Decision: Preserve all records. Do not classify individual
zero-value voucher entries as failed payments without
additional evidence.

## 3. Timestamp anomalies

Three categories of order anomalies were identified:

| Rule | Affected records |
|---|---:|
| Approval after carrier handover | 1,359 |
| Carrier handover after customer delivery | 23 |
| Delivered order missing customer delivery timestamp | 8 |

These records are preserved and flagged in the processed
orders dataset.

No timestamps are automatically corrected or fabricated.

## 4. Geolocation duplicates

The original geolocation dataset contained 1,000,163 rows.
After removing 261,831 exact duplicate rows, 738,332 rows
remain.

Multiple coordinate combinations per postcode are retained
because a postcode may represent a geographic area rather
than a single point.

## 5. Missing values

Missing values in reviews, orders and products are retained.
They are not automatically replaced with fabricated values.

Product records with incomplete descriptive or physical
attributes are flagged for downstream analysis.

## 6. Quality management principles

- Preserve source information.
- Distinguish legitimate exceptions from data errors.
- Apply reproducible validation rules.
- Investigate anomalies before making corrections.
- Make quality findings available to downstream reporting.

### Product category translation coverage

- Total products: 32,951
- Products with English translations: 32,328
- Products with missing source categories: 610
- Products with categories lacking English translations: 13

The 13 untranslated products belong to:
- portateis_cozinha_e_preparadores_de_alimentos: 10
- pc_gamer: 3

No category translations were fabricated. Original category values
were preserved, and missing translations remain NULL.



## Payment Data Quality Findings

### 1. Credit-card instalment anomalies

Two payment records have zero instalments despite being
classified as credit-card payments.

| Payment type | Invalid instalments | Records |
|---|---:|---:|
| credit_card | 0 | 2 |

Treatment:
- Preserve original payment values.
- Do not replace zero instalments with one.
- Flag both records for investigation.

### 2. Delivered order without payment

Order ID:
`bfbd0f9bdef84302105ad712db648a6c`

Investigation findings:

- Order status: delivered
- Number of order items: 3
- Item value: R$134.97
- Freight value: R$8.49
- Payment records: 0
- Payment value: R$0.00

The order exists in the original raw orders dataset.
It is marked as delivered and has three associated order items,
but no corresponding payment record exists.

Treatment:
- Preserve the order and its associated order items.
- Do not generate a synthetic payment record.
- Flag the order as a payment-data completeness exception.
- Investigate the discrepancy before drawing financial conclusions.


### 3. Repeated Review Identifiers

Investigation identified 789 review ID groups appearing more than once,
representing 814 excess review records.

- Total review records: 99,224
- Distinct review IDs: 98,410
- Repeated review ID groups: 789
- Maximum occurrences of a review ID: 3

Investigation of sample records showed that repeated review IDs can
be associated with different order IDs.

Treatment:
- Preserve all review records.
- Use staging_review_id as the unique record identifier.
- Retain review_id as the original source identifier.
- Do not remove records solely because review_id is repeated.
- Investigate differences in review content before classifying
  repeated identifiers as duplicate reviews.


### Repeated Review Identifiers

- Total review records: 99,224
- Distinct review identifiers: 98,410
- Repeated review ID groups: 789
- Excess records associated with repeated IDs: 814
- Maximum occurrences of a review ID: 3

Investigation found repeated review IDs associated with different orders.
Sampled groups had consistent review scores and comment fields, including
NULL comment values.

These records cannot be classified as duplicate records based on review_id
alone. All records were retained, with staging_review_id used as the
unique record identifier.


## Orders with Payments but No Order Items

Investigation identified 8 orders without associated order-item records
in both the analytics fact table and the original raw source table.

| Order Status | Orders | Payment Records | Payment Value |
|---|---:|---:|---:|
| Created | 5 | 5 | R$688.10 |
| Invoiced | 2 | 2 | R$149.23 |
| Shipped | 1 | 1 | R$77.73 |
| Total | 8 | 8 | R$915.06 |

Findings:
- All 8 orders have payment records.
- All 8 have zero matching records in raw.order_items.
- All 8 have zero matching records in analytics.fact_order_items.
- The issue originates in the source dataset, not the staging or analytics loading process.
- The underlying reason for these inconsistencies cannot be established from the available data.

Treatment:
- Preserve all 8 orders and their payment records.
- Do not fabricate missing order items.
- Do not remove payment records or assume they are invalid.
- Classify these records as source-level order-to-item reconciliation exceptions.


### Credit Card Instalment and Payment Discrepancy Analysis

An investigation of 71,841 delivered orders with exactly one credit-card payment identified 261 payment discrepancies (0.363%).

Discrepancy rates increased across instalment groups:

| Instalment group | Orders | Discrepancies | Rate |
|---|---:|---:|---:|
| 1 | 23,113 | 8 | 0.035% |
| 2–3 | 21,719 | 47 | 0.216% |
| 4–6 | 15,465 | 102 | 0.660% |
| 7–12 | 11,373 | 99 | 0.870% |
| More than 12 | 171 | 5 | 2.924% |

Two logistic regression models were fitted, using one instalment as the reference category:

- Model 1 adjusted for continuous log-transformed order value.
- Model 2 adjusted for categorical order-value quartiles.

Both models showed a persistent positive association between instalment group and payment discrepancy odds. For example, the adjusted odds ratio for 7–12 instalments was 87.37 in Model 1 and 94.35 in Model 2.

All instalment-group coefficients were statistically significant at p < 0.001. However, the models exhibited low explanatory power and potential overdispersion. The reference group contained only eight discrepancy events, and the more-than-12 instalment group contained only five.

**Interpretation:** The analysis identifies a strong association between instalment count and payment discrepancies in this dataset, even after adjustment for order value. It does not establish causation. Further model diagnostics and sensitivity analysis are required before treating the estimates as definitive.

The underlying payment records should be retained unchanged while the discrepancies are investigated. No payment values should be artificially adjusted to force reconciliation.


### Repeated Products Within Orders

During investigation of large payment discrepancies, repeated product and seller combinations were identified within individual orders.

Two examples were verified directly against `raw.order_items`:

- Order `6e5fe7366a2e1bfbf3257dba0af1267f` contains six item records representing two distinct products, each repeated three times.
- Order `bc2c82b0ef78d2252b6176d1972db7c9` contains three records for the same product and seller.

Each record has a distinct `order_item_id`, and the records are present in the original source dataset.

**Treatment:** Retain all records. Do not classify repeated product/seller combinations as duplicate transactions solely because their descriptive and financial attributes match. The composite key `(order_id, order_item_id)` remains the appropriate order-item identifier.


### Delivered Credit-Card Payment Discrepancy Investigation

The investigation covered 71,841 delivered orders with exactly one credit-card payment and valid positive instalment counts.

A total of 261 orders (0.363%) had payment values differing from expected order values, calculated as the sum of item prices and freight charges.

**Discrepancy direction:**

- 235 orders (90.0%) had payments above expected order value.
- 26 orders (10.0%) had payments below expected order value.

The aggregate signed difference across the discrepant orders was approximately R$2,836.45, based on the displayed grouped results.

**Observed percentage clusters:**

| Group | Orders | Direction | Net difference |
|---|---:|---|---:|
| Approximately 13% | 56 | Above | R$1,070.16 |
| Approximately 15.5% | 38 | Above | R$575.30 |
| Approximately 7% | 22 | Above | R$131.22 |
| Other | 119 | Above | R$1,206.75 |
| Other | 26 | Below | -R$146.99 |

The percentage clusters were observed by comparing recorded payment values with item-plus-freight totals. They do not establish financing rates or explain the underlying cause of the differences.

Additional investigation of the eight largest discrepancies identified single-item and multi-item orders, repeated product/seller combinations already present in the raw source, substantial freight contributions in some orders, and orders involving multiple sellers.

**Treatment and recommendations:**

- Preserve original payment and order-item records.
- Do not artificially adjust payment values to force reconciliation.
- Retain order-level discrepancy flags and investigate material exceptions.
- Obtain additional payment or financing information before attributing discrepancies to interest or fees.
- Use the findings as indicators for payment reconciliation controls, not proof of financial misconduct or incorrect charges.




### Delivery Performance Investigation – February to March 2018

An investigation of 96,478 delivered orders identified a deterioration in delivery performance during February and March 2018. The overall late-delivery rate reached 15.99% in February and peaked at 21.36% in March, compared with 6.56% in January.

Stage-level analysis identified the carrier-to-customer interval as the largest observed contributor to longer delivery durations. Average post-handover delivery time increased from 10.48 days in January to 13.38 days in February and remained elevated at 12.97 days in March.

The difference was particularly pronounced when comparing late and on-time orders. In March, median carrier-to-customer duration was 26.73 days for late orders versus 7.84 days for on-time orders. The 90th-percentile durations were 42.86 and 17.44 days, respectively.

Geographic and seller-level analysis also identified substantial variation across shipping lanes. In March, SP-to-RJ recorded 44.67% late deliveries, SP-to-CE 56.58%, and SP-to-PA 53.70%. Several sellers experienced elevated late-delivery rates simultaneously, indicating that the deterioration was not isolated to a single seller.

**Business implication:** Logistics management should investigate carrier handover and post-handover delivery performance, prioritising high-volume routes with elevated late-delivery rates. Seller performance should be monitored by destination route and order volume rather than through overall seller averages alone.

**Analytical limitation:** The available dataset establishes associations and historical patterns, but does not identify the underlying operational cause. Carrier capacity, route conditions, and distribution-centre performance require additional operational data to verify.