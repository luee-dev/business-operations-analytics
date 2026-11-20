# Business Operations & Performance Analytics

## SQL Business Analysis Report

**Project:** Business Operations & Performance Analytics Platform\
**Dataset:** Olist Brazilian E-Commerce Public Dataset\
**Analysis period:** September 2016 -- October 2018 (observed order
activity)\
**Technology:** PostgreSQL, SQL, Python/Pandas, Power BI (planned
downstream layer)\
**Status:** SQL analytics and cross-functional view validation complete

------------------------------------------------------------------------

## 1. Executive summary

This project develops an analytical data platform for examining the
operational and commercial performance of a multi-seller e-commerce
marketplace. The SQL layer transforms the source data into a dimensional
model and a set of reusable analytical views covering order performance,
customers, acquisition and retention, products and categories, sellers,
payments, delivery, and customer reviews.

The analysis covers 99,441 orders, 112,650 order-item lines, 103,886
payment records, 99,224 review records, 32,951 products, 3,095 sellers,
and 99,441 customer records. The data is historical: the observed order
activity runs from September 2016 through October 2018. It should
therefore be interpreted as a case study of marketplace operations
during that period, not as a description of current Olist performance or
the current Brazilian e-commerce market.

The main operational finding is the relationship between delivery
performance and customer satisfaction. Among reviewed orders eligible
for delivery-timeliness comparison, late orders had an average review
score of 2.57 and a negative-review rate of 53.99%, compared with 4.29
and 9.19% for on-time orders. This is a strong association and a useful
operational prioritisation signal, but it does not establish that
lateness alone caused a poor review.

Customer analysis indicates a highly one-time-purchase customer base:
90,557 of 93,358 customers with at least one delivered order made only
one delivered purchase. The repeat-purchase rate was 3.00% under the
defined customer-level methodology. Repeat customers generated
approximately 1.92 times the cumulative delivered value per customer of
one-time customers, primarily because they made more purchases; their
average order value was not higher.

The SQL analytical layer is supported by reconciliation checks. The five
cross-functional views were independently checked against their
underlying analytical facts. The final customer-segment/category
validation covered 521 combinations and returned zero mismatches across
customer counts, order counts, item lines, delivered lines, product
value, delivered value, and delivered value per order.

------------------------------------------------------------------------

## 2. Business context and analytical objectives

A marketplace operation depends on several connected processes:

-   Customer acquisition, repeat purchasing, and customer value.
-   Product and category assortment, sales contribution, and catalogue
    completeness.
-   Seller participation, sales contribution, and fulfilment
    performance.
-   Order processing, delivery timeliness, and payment collection.
-   Customer experience as reflected in review scores.

These processes should not be analysed in isolation. A delayed order may
be associated with a poor review; category mix may influence operational
workload; seller-level delivery patterns may help identify areas for
investigation; and customer segments may have different category
preferences.

The SQL analysis was designed to answer questions such as:

1.  How are orders, delivered sales, cancellations, and delivery
    performance changing over time?
2.  How concentrated are sales across customers, products, categories,
    and sellers?
3.  How many customers return to make additional purchases, and how does
    customer value differ by purchase frequency?
4.  Which product categories contribute most to delivered product value?
5.  How do delivery outcomes relate to customer review scores?
6.  Do payment methods or installment groups show differences in
    delivery outcomes or payment discrepancies?
7.  Which seller and category combinations warrant further operational
    investigation?

The objective is descriptive and diagnostic analytics: establish
reliable measures, identify patterns, and provide evidence for
prioritising further investigation.

------------------------------------------------------------------------

## 3. Dataset and scope

The project uses the Olist Brazilian E-Commerce Public Dataset. It
contains related CSV datasets for customers, orders, order items,
payments, reviews, products, sellers, geolocation, and product-category
translations.

### 3.1 Data volume

  Dataset                  Loaded records / retained records
  ---------------------- -----------------------------------
  Customers                                           99,441
  Geolocation                                        738,332
  Order items                                        112,650
  Payments                                           103,886
  Reviews                                             99,224
  Orders                                              99,441
  Products                                            32,951
  Sellers                                              3,095
  Category translation                                    71

The geolocation source contained 1,000,163 rows. Exact duplicate rows
were removed during preparation, leaving 738,332 retained records.
Multiple valid coordinate combinations for a postcode were not treated
as duplicates merely because the postcode repeated.

### 3.2 Scope and caveats

-   Order activity is historical, with the observed order timeline
    spanning September 2016 to October 2018.
-   The date dimension covers September 4, 2016 to April 9, 2020 because
    it includes the range required by the available date attributes;
    this does not mean orders occurred throughout that entire period.
-   The dataset is observational. Associations between delivery,
    reviews, categories, and sellers do not prove causation.
-   Monetary values are reported in Brazilian reais (R\$), as
    represented in the source data.
-   Measures such as seller-order associations and category-order
    associations are not always unique marketplace-order counts. Orders
    may contain items from multiple sellers or multiple categories.
-   Recent customer cohorts have less observation time in which to make
    repeat purchases. Cohort comparisons should account for this
    exposure difference.

------------------------------------------------------------------------

## 4. Data architecture and analytical model

The database is organised into three schemas:

  Schema        Purpose
  ------------- -------------------------------------------------
  `raw`         Landing area for source data
  `staging`     Prepared and typed source tables
  `analytics`   Dimensional model and reusable analytical views

The analytics schema uses a dimensional/star-style model with conformed
dimensions and facts.

### 4.1 Dimensions

-   `dim_customers`: customer-level descriptive attributes and customer
    identifiers.
-   `dim_date`: calendar attributes used for consistent time analysis.
-   `dim_products`: product attributes and translated category labels.
-   `dim_sellers`: seller descriptive attributes and location
    information.

### 4.2 Facts

-   `fact_orders`: order-level records and order lifecycle attributes.
-   `fact_order_items`: order-item-level product, seller, price,
    freight, and shipping-limit data.
-   `fact_payments`: payment transaction records.
-   `fact_reviews`: review records and review scores.

The model preserves the different grains of the source processes. This
is important because joining order items directly to payments or reviews
can multiply rows and inflate sums. Where order-level measures are
required alongside item-level measures, the analysis aggregates each
process to the intended grain before joining.

### 4.3 Core reconciliation totals

  Measure                              Validated total
  --------------------------------- ------------------
  Orders                                        99,441
  Delivered orders                              96,478
  Canceled orders                                  625
  Shipped orders                                 1,107
  Order-item lines                             112,650
  Delivered item lines                         110,197
  Product value across item lines     R\$13,591,643.70
  Delivered product value             R\$13,221,498.11
  Freight value across item lines      R\$2,251,909.54
  Delivered freight value              R\$2,198,275.64
  Payment records                              103,886
  Total payment value                 R\$16,008,872.12
  Review records                                99,224

The delivered product value and payment value are different measures.
They should not be treated interchangeably, nor should either be
described as profit. The project does not calculate full marketplace
profitability because the dataset does not provide all required cost
components.

------------------------------------------------------------------------

## 5. Data quality and validation

Data quality checks were performed before and during analytical
modelling. The approach was to identify, quantify, and preserve source
anomalies rather than silently modify records or manufacture missing
values.

### 5.1 Key findings from data quality assessment

-   **Order timestamps:** 1,359 orders had approval timestamps after
    carrier hand-off; 23 had carrier hand-off after customer delivery; 8
    delivered orders lacked a delivery timestamp. In total, 1,390 orders
    had at least one of the identified timestamp anomalies.
-   **Products:** 610 products had incomplete descriptive metadata, and
    2 had incomplete physical-measurement information. The 610
    incomplete-metadata products were in the uncategorized group used by
    the analysis.
-   **Reviews:** 99,224 review records contained 98,410 distinct review
    IDs. Repeated review IDs were not assumed to be exact duplicate
    records; all source review records were preserved.
-   **Payments:** 9 zero-value payment rows and 2 invalid installment
    records were retained and flagged.
-   **Orders without payment:** 1 delivered order had no associated
    payment record. No synthetic payment was created.
-   **Orders without items:** 775 orders had no item lines. Most were
    unavailable or canceled. Eight created/invoiced/shipped orders had
    payment records but no item lines; these were preserved for
    investigation.
-   **Geolocation:** exact duplicate rows were removed while valid
    multiple coordinate combinations were retained.

### 5.2 Validation approach

The validation process included:

-   Row-count and distinct-key checks.
-   Duplicate-grain checks for analytical views.
-   Null and invalid-value checks for critical attributes.
-   Reconciliation of fact totals to source and analytical outputs.
-   Independent source-to-view aggregation comparisons.
-   Explicit review of exceptions and interpretation risks.

The quality assessment recorded 9 critical checks as passed, 34 error
checks as passed, and 2 warnings. Warnings and anomalies were not
automatically treated as fatal errors; they were retained as documented
limitations or investigation items.

------------------------------------------------------------------------

## 6. SQL analytical views and their grains

The SQL analytics layer creates reusable views for reporting and
downstream visualisation. Each view has a defined grain so users can
understand what one row represents and avoid invalid aggregation.

### 6.1 Order performance

**View:** `analytics.vw_order_performance`\
**Grain:** One row per order.

The view consolidates order attributes with item and payment aggregates.
Item and payment processes are aggregated separately before joining,
preventing item-payment row multiplication.

Key checks: - 99,441 rows and 99,441 distinct orders. - No duplicate
order grain. - 775 orders without item lines. - 1 order without a
payment record. - No missing estimated delivery dates in the view.

The view is the central source for order-level operational measures such
as order status, product value, freight, expected order value, payment
value, payment difference, and delivery dates.

### 6.2 Monthly performance

**View / analysis:** Monthly order and operational performance.

The monthly analysis reconciles to 99,441 orders, including 96,478
delivered, 625 canceled, and 1,107 shipped orders. It identifies changes
in order volume and delivery performance over the observation period.

Across delivered orders, 7,826 were classified as late, giving an
overall late-delivery rate of approximately 8.11% using the defined
eligible delivered-order denominator. March 2018 had a notably high
late-delivery rate of 21.36%, followed by February 2018 at 15.99%.
January 2018 was 6.56%, April 2018 was 5.31%, and June 2018 was 1.36%.

September and October 2018 are partial months in the available order
history, so their totals should not be compared directly with complete
months without accounting for the shorter observation window.

### 6.3 Customer performance and RFM

**Views:** `analytics.vw_customer_performance`,
`analytics.vw_customer_rfm`\
**Grain:** One row per `customer_unique_id`.

Customer analysis distinguishes customer records from unique customer
identities. The source contains 99,441 customer records and 96,096
distinct customer unique IDs.

RFM analysis uses: - **Recency:** days since the customer's most recent
delivered purchase, relative to the analysis reference date. -
**Frequency:** number of delivered purchases. - **Monetary:** delivered
purchase value.

Each RFM dimension is scored from 1 to 5. The segment rules identify
Champions, At Risk, Inactive / Hibernating, Recent High-Value Customers,
Potential High Value, Loyal Customers, and Regular Customers. The
resulting RFM population contains 93,358 customers with at least one
delivered purchase; customers without a qualifying RFM record are
handled as unclassified in cross-functional analysis.

Segment totals reconcile to 93,358 customers, 96,478 delivered orders,
and R\$15,419,773.75 in delivered order value.

  Customer segment                Customers   Delivered orders   Delivered value
  ----------------------------- ----------- ------------------ -----------------
  Inactive / Hibernating             36,392             36,392   R\$5,887,396.64
  Regular Customers                  32,859             32,859   R\$2,385,308.48
  Potential High Value               14,380             14,380   R\$3,169,074.97
  Recent High-Value Customers         6,926              6,926   R\$3,113,806.20
  Champions                             983              2,145     R\$366,509.87
  At Risk                               997              2,075     R\$294,507.02
  Loyal Customers                       821              1,701     R\$203,170.57

The segment labels are rule-based analytical classifications, not labels
supplied by Olist. The RFM reference date and scoring rules should be
stated whenever the segments are reused.

### 6.4 Repeat purchase and customer value

Of 96,096 unique customers, 93,358 had at least one delivered order.
Among those 93,358 customers: - 90,557 made one delivered purchase. -
2,801 made more than one delivered purchase. - The repeat-customer rate
was 3.00%.

One-time customers generated R\$14,555,586.29 in delivered value,
averaging R\$160.73 per customer. Repeat customers generated
R\$864,187.46 across 5,921 delivered orders, averaging R\$308.53 per
customer. This is approximately 1.92 times the average cumulative
customer value of one-time customers.

However, average order value was R\$160.73 for one-time customers and
R\$145.85 for repeat customers. The higher cumulative value of repeat
customers is therefore associated with more purchases, not a higher
average order value.

The repeat-purchase interval analysis covered 2,801 repeat customers and
3,120 purchase intervals. The average of each customer's average
interval was 80.97 days; the median customer-average interval was 32.82
days. The 90th percentile was 238.76 days, indicating a long tail in
repeat-purchase timing.

### 6.5 Cohort and acquisition analysis

**Views:** `analytics.vw_customer_acquisition` and cohort analysis
outputs.\
**Grain:** Customer acquisition month and cohort month offset.

Acquisition is defined by the month of the customer's first delivered
purchase. The acquisition view covers 24 cohort months from September
2016 through August 2018, with 93,358 customers.

The cohort retention analysis uses monthly activity retention: the
percentage of a cohort that made a delivered purchase in a given month
offset. It is not continuous retention. Weighted monthly activity
retention falls from 100% in month zero to 0.48% in month one, 0.34% in
month two, and 0.25% in month three. Later-month rates remain low, with
the cohort population and exposure period varying by cohort age.

The acquisition analysis also distinguishes first-month acquisition
activity from subsequent observed purchases. It recorded 94,579
first-month orders and R\$15,139,052.21 in first-month value, with an
additional 1,899 observed orders and R\$280,721.54 in value beyond that
first month. These are historical observed totals, not a forecast of
future customer value. Newer cohorts have had less time to generate
repeat purchases.

### 6.6 Product and category performance

**Views:** `analytics.vw_product_performance`,
`analytics.vw_category_performance`\
**Grain:** One row per product or one row per product category.

The product analysis contains 32,951 products. The order-item facts
contain 112,650 item lines, with R\$13,591,643.70 in total product value
and R\$2,251,909.54 in freight. Delivered item lines account for 110,197
lines, R\$13,221,498.11 in product value, and R\$2,198,275.64 in
freight.

Leading categories by delivered product value were:

  -----------------------------------------------------------------------
  Category              Delivered product value        Share of delivered
                                                            product value
  ------------------- ------------------------- -------------------------
  Health & beauty               R\$1,233,131.72                     9.33%

  Watches & gifts               R\$1,166,176.98                     8.82%

  Bed, bath & table             R\$1,023,434.76                     7.74%

  Sports & leisure                R\$954,852.55                     7.22%

  Computers &                     R\$888,724.61                     6.72%
  accessories                                   
  -----------------------------------------------------------------------

The top five categories contributed 39.83% of delivered product value;
the top ten contributed 62.43%.

At product level, the top ten products contributed 3.35% of delivered
product value, the top 20 contributed 5.45%, and the top 50 contributed
9.38%. The category-level Herfindahl-Hirschman Index (HHI) was 489.42,
indicating that delivered value was distributed across a broad set of
categories rather than dominated by a small number of categories.

Some categories have elevated cancellation percentages but very small
order counts. For example, the pc_gamer category had a 12.5%
cancellation rate across 8 orders. Such rates should be interpreted with
sample size in mind and not used alone to make assortment decisions.

### 6.7 Seller performance

**Views:** `analytics.vw_seller_order_performance`,
`analytics.vw_seller_performance`\
**Grain:** One row per seller-order association and one row per seller,
respectively.

Seller analysis includes seller-associated order activity, item lines,
product and freight value, delivered performance, shipping-limit
measures, and delivery timing.

The seller-level totals reconcile to the item facts: - 112,650 item
lines. - 110,197 delivered item lines. - R\$13,591,643.70 total product
value. - R\$13,221,498.11 delivered product value. - R\$2,251,909.54
total freight value. - R\$2,198,275.64 delivered freight value.

The top ten sellers accounted for 13.27% of delivered seller-associated
sales, the top 20 for 21.28%, and the top 50 for 33.20%.

A seller-order association is not necessarily a unique marketplace
order: an order may contain items from more than one seller. In
addition, delivery timestamps are order-level timestamps. Applying an
order's delivery outcome to each associated seller does not prove that a
particular seller caused a delay. Seller comparisons should be used to
identify cases for investigation, with suitable volume thresholds and
operational context.

### 6.8 Cross-functional analysis

Five views connect operational, financial, customer, and product
dimensions.

#### `analytics.vw_order_review_performance`

**Grain:** One row per order.

Combines order performance with review information while preserving the
order grain. It contains 99,441 orders and reconciles to 99,224 review
records. There are 768 orders without scored reviews and without review
records in the order-level view.

#### `analytics.vw_delivery_review_analysis`

**Grain:** Delivery classification.

Compares review outcomes across late, on-time, and not-eligible delivery
groups.

  -----------------------------------------------------------------------
  Delivery group    Reviewed orders     Average review    Negative-review
                                                 score               rate
  -------------- ------------------ ------------------ ------------------
  Late                        7,661               2.57             53.99%

  On time                    88,163               4.29              9.19%

  Not eligible    2,849 reviewed in               1.75             77.86%
                        the earlier                    
                      not-delivered                    
                         comparison                    
  -----------------------------------------------------------------------

The final view's `Not eligible` group includes all orders that do not
qualify for the late/on-time comparison, not only not-delivered orders.
The earlier not-delivered-only comparison is therefore a narrower
population. The late group has approximately 5.9 times the
negative-review rate of the on-time group.

Delay severity analysis further shows that negative reviews increase as
delivery delay increases: - 1--3 days late: 19.08% negative reviews. -
4--7 days late: 61.25%. - 8--14 days late: 78.03%. - 15 or more days
late: 78.66%.

The pattern suggests that even moderate delays may materially affect
customer experience, while the negative-review rate levels off at a high
level for delays of eight days or more. This remains an observational
relationship.

#### `analytics.vw_category_review_analysis`

**Grain:** One row per category.

Connects category performance with order review and delivery outcomes.
It contains 74 categories. Financial and item-line measures reconcile to
the underlying item facts: 112,650 item lines, R\$13,591,643.70 product
value, and R\$2,251,909.54 freight.

For category-level review analysis, an order containing multiple
categories can contribute to multiple category-order associations.
Category-level order and review counts must therefore not be summed and
presented as unique marketplace totals.

Examples among high-volume categories: - Bed, bath & table: 788 late
reviewed orders; 55.84% negative reviews on late orders versus 12.15% on
on-time orders. - Health & beauty: 758 late reviewed orders; 52.11%
versus 7.48%. - Sports & leisure: 575 late reviewed orders; 56.17%
versus 7.64%. - Furniture & decor: 526 late reviewed orders; 54.37%
versus 11.72%. - Watches & gifts: 456 late reviewed orders; 56.80%
versus 9.75%.

These comparisons can help prioritise categories for fulfilment
investigation, but do not establish that category characteristics caused
the delay or review outcome.

#### `analytics.vw_payment_delivery_analysis`

**Grain:** Payment type × installment group.

The view contains 17 distinct groups and reconciles to the
order-performance view. An independent comparison checked total orders,
delivered orders, canceled orders, delivery-eligible orders, late
orders, late-delivery percentage, payment value, average payment,
average payment difference, discrepancy counts, and average delivery
days. All 12 metric comparisons matched across all 17 groups.

Examples: - Boleto, one installment: 19,784 orders; 8.88% late among
eligible orders. - Credit card, one installment: 23,805 orders; 7.26%
late. - Credit card, two to three installments: 22,440 orders; 8.10%
late. - Credit card, four to six installments: 15,995 orders; 8.24%
late. - Credit card, seven to twelve installments: 11,840 orders; 8.76%
late.

There is no clear monotonic relationship between installment group and
late-delivery rate in these results. Payment type and installment count
should not be interpreted as causes of delivery performance. Combined
payment-type labels can represent orders paid using multiple methods;
the view is not at individual payment-transaction grain.

Across the full order population, 303 orders were flagged with a payment
discrepancy using the view's defined threshold of an absolute payment
difference greater than R\$0.01. The total payment value reconciles to
R\$16,008,872.12.

#### `analytics.vw_customer_segment_category_analysis`

**Grain:** Customer segment × product category.

The view contains 521 unique segment/category combinations. It connects
RFM customer segments to category purchasing behaviour. An independent
source-to-view reconciliation returned zero mismatches for: - Distinct
customers. - Distinct orders. - Item lines. - Delivered item lines. -
Total product value. - Delivered product value. - Delivered value per
order.

A customer can purchase across multiple categories and therefore appear
in multiple segment/category combinations. Summing `distinct_customers`
across categories does not yield unique customers for the segment.
Similarly, an order can contain products from several categories and
appear in more than one category row.

The `Unclassified` segment represents customers without a matching RFM
segment in the left join. It should not be interpreted as a
customer-value segment in its own right.

------------------------------------------------------------------------

## 7. Business insights and recommendations

The following recommendations are derived from descriptive patterns in
the historical data. They should be treated as hypotheses and
prioritisation opportunities for further operational analysis.

### 7.1 Prioritise delivery reliability as a customer-experience initiative

Late orders have a substantially higher negative-review rate than
on-time orders. The deterioration is particularly pronounced once delays
exceed three days.

**Recommended actions:** - Track late-delivery rate and delay severity
by month, seller, category, and destination. - Establish alerts for
orders approaching or exceeding estimated delivery dates. - Investigate
the operational causes of delays rather than attributing them
automatically to sellers. - Monitor negative-review rate alongside
delivery KPIs to assess whether operational improvements coincide with
better customer experience.

### 7.2 Investigate high-volume category delivery exceptions

Categories such as bed, bath & table; health & beauty; sports & leisure;
furniture & decor; and watches & gifts have both meaningful delivered
sales contribution and material volumes of late reviewed orders.

**Recommended actions:** - Prioritise high-volume categories with
elevated late-order negative-review counts. - Compare category-level
delivery performance across sellers, regions, and order periods. - Use
both absolute counts and rates so that low-volume categories do not
dominate decisions based on unstable percentages.

### 7.3 Strengthen repeat-purchase analysis and customer lifecycle measurement

Only 3.00% of customers with delivered purchases were repeat customers
under this analysis definition. Repeat customers generated higher
cumulative customer value because they placed more orders.

**Recommended actions:** - Analyse customer journeys and
time-to-second-purchase. - Test post-purchase engagement and retention
initiatives. - Compare cohorts using equal observation windows. -
Monitor repeat purchase rate, time between purchases, and cumulative
customer value as separate measures.

The historical data does not establish why customers did not return.
Further research would be required to distinguish product, pricing,
delivery, service, and market factors.

### 7.4 Use category contribution and concentration to guide assortment reviews

The top five categories generated 39.83% of delivered product value,
while the top 50 products generated 9.38%.

**Recommended actions:** - Monitor category contribution and
product-level concentration together. - Review catalogue completeness
for products with missing descriptive metadata. - Investigate categories
with high cancellation rates using minimum-volume thresholds. - Avoid
reducing assortment solely because a category has a high percentage
derived from a very small sample.

### 7.5 Use seller metrics as investigation signals, not automatic performance verdicts

Seller sales are distributed across a broad population, with the top 50
sellers accounting for 33.20% of delivered seller-associated sales.

**Recommended actions:** - Build seller scorecards with order volume,
delivered value, late rate, cancellation rate, and review outcomes. -
Apply minimum sample-size requirements before ranking sellers. -
Separate seller-controlled dispatch measures from carrier and
order-level delivery outcomes where the data allows. - Investigate
outliers with operational context before taking action.

### 7.6 Monitor payment reconciliation independently of fulfilment

The payment analysis identified 303 orders with a payment difference
greater than R\$0.01 under the selected rule.

**Recommended actions:** - Maintain a payment reconciliation exception
queue. - Investigate discrepancies by payment method, installment group,
order status, and transaction count. - Keep payment transaction grain
separate from order-level payment summaries. - Do not infer that payment
method or installment choice causes delivery outcomes from the
descriptive comparisons.

------------------------------------------------------------------------

## 8. Validation evidence and completion status

The analytical views were checked for expected grain, key uniqueness,
completeness, and reconciliation to their source facts.

### 8.1 Cross-functional view validation

  -----------------------------------------------------------------------------------------
  View                                      Validation evidence     Result
  ----------------------------------------- ----------------------- -----------------------
  `vw_order_review_performance`             99,441 rows; 99,441     Passed
                                            distinct orders;        
                                            review-record           
                                            reconciliation          

  `vw_delivery_review_analysis`             Delivery-group totals   Passed
                                            reconcile to 99,441     
                                            orders; reviewed-order  
                                            and review metrics      
                                            inspected               

  `vw_category_review_analysis`             74 category rows;       Passed
                                            item-line,              
                                            product-value, freight, 
                                            product-count, and      
                                            review metrics          
                                            reconciled              

  `vw_payment_delivery_analysis`            17 groups; independent  Passed
                                            comparison of 12        
                                            metrics; all mismatches 
                                            zero                    

  `vw_customer_segment_category_analysis`   521 groups; independent Passed
                                            comparison of 8         
                                            metrics; all mismatches 
                                            zero                    
  -----------------------------------------------------------------------------------------

### 8.2 Final customer-segment/category reconciliation

The final independent source-to-view check returned:

  Check                                Result
  ---------------------------------- --------
  Groups checked                          521
  Missing view groups                       0
  Customer count mismatches                 0
  Order count mismatches                    0
  Item line mismatches                      0
  Delivered line mismatches                 0
  Product value mismatches                  0
  Delivered value mismatches                0
  Delivered value/order mismatches          0

This is evidence that the view's segment/category aggregation agrees
with an independently rebuilt aggregation over the underlying facts and
dimensions.

### 8.3 SQL phase status

The SQL analytical phase is complete: - Dimensional model created. -
Core order performance view established. - Customer, cohort,
acquisition, product, category, and seller analyses developed. - Five
cross-functional views created and validated. - Key measures reconciled
to the underlying facts. - Grain and interpretation caveats documented.

------------------------------------------------------------------------

## 9. Limitations and responsible interpretation

1.  **Historical coverage:** The dataset represents activity from
    2016--2018. Results are not current operational benchmarks.
2.  **Observational analysis:** Correlation and group differences do not
    establish causation.
3.  **Multi-seller orders:** Seller-order associations can exceed unique
    marketplace orders.
4.  **Multi-category orders:** Category-order associations can exceed
    unique marketplace orders.
5.  **Order-level delivery timestamps:** Delivery outcomes attached to
    seller associations do not establish seller responsibility.
6.  **Customer cohort exposure:** Newer cohorts have less time to
    generate repeat purchases.
7.  **Small samples:** High percentages based on a small number of
    orders are unstable and require caution.
8.  **Payment versus sales value:** Payment value, product value,
    freight, and profit are distinct concepts. The dataset does not
    provide a complete cost model for profitability.
9.  **RFM definitions:** Segment membership depends on the chosen
    reference date, scoring method, and business rules.
10. **Missing and anomalous source data:** Identified anomalies were
    preserved and flagged; they may affect specific analyses.

------------------------------------------------------------------------

## 10. Next phase

With the SQL layer validated and documented, the next phase is Python
analytics. Python will complement SQL by providing reproducible
analytical workflows, statistical exploration, and potentially reusable
reporting outputs.

The next phase should build on the validated SQL views rather than
reimplementing business logic inconsistently. Candidate work includes: -
A Python analysis package that connects to PostgreSQL and retrieves
curated analytical views. - Reproducible exploratory and statistical
analysis. - Automated checks for key analytical metrics. - Exportable
business summaries and charts. - A clear hand-off of curated datasets to
Power BI.

The SQL views remain the source of truth for the defined business
metrics unless a documented analytical requirement justifies changing
them.

------------------------------------------------------------------------

## Appendix A. Key metric definitions

  -----------------------------------------------------------------------
  Metric                              Definition used in this project
  ----------------------------------- -----------------------------------
  Delivered order                     Order with
                                      `order_status = 'delivered'`

  Late delivered order                Eligible delivered order whose
                                      delivery timestamp is later than
                                      the estimated delivery date

  Negative review                     Review score less than or equal to
                                      2

  Average order value                 Delivered order value divided by
                                      delivered order count, at the
                                      stated grain

  Repeat customer                     Customer with more than one
                                      delivered purchase

  Customer recency                    Days since most recent delivered
                                      purchase relative to the analysis
                                      reference date

  Customer frequency                  Count of delivered purchases

  Customer monetary value             Sum of delivered purchase value

  Payment discrepancy                 Absolute payment difference greater
                                      than R\$0.01

  Delivered value per                 Delivered product value divided by
  category/segment order              distinct delivered orders within
                                      the segment/category group
  -----------------------------------------------------------------------

Metric denominators must be retained when comparing rates. In
particular, late-delivery rates use delivery-eligible orders, while
customer, seller, and category analyses may use different association
grains.

## Appendix B. Suggested repository structure

``` text
business-operations-analytics/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
├── reports/
│   ├── product_category_analysis.md
│   └── sql_business_analysis.md
├── sql/
│   ├── analytics/
│   ├── ddl/
│   ├── staging/
│   └── validation/
├── src/
├── tests/
└── README.md
```
