# Customer Experience and Delivery Performance Analysis

## 1. Objective

Evaluate the relationship between delivery performance and customer review outcomes using order-level data.

The analysis compares late and on-time delivered orders to determine whether delivery delays are associated with poorer customer feedback.

## 2. Data and Methodology

- Source: `analytics.vw_order_review_performance`
- Source grain: one row per order.
- Total orders: 99,441.
- Eligible orders: 95,824.
- Late orders: 7,661.
- On-time orders: 88,163.

Eligible orders were restricted to:
- Delivered orders.
- Orders with a valid late/on-time classification.
- Orders with at least one scored review.

Orders without a scored review or valid delivery classification were excluded.

An order was classified as having a negative review if it contained at least one negative review record. Each order contributed only once to the negative-review order rate.

## 3. Delivery and Review Performance

| Metric | Late delivery | On-time delivery |
|---|---:|---:|
| Orders | 7,661 | 88,163 |
| Average review score | 2.57 | 4.29 |
| Median review score | 2.00 | 5.00 |
| Negative-review orders | 4,146 | 8,164 |
| Negative-review order rate | 54.12% | 9.26% |
| 95% Wilson confidence interval | 53.00%–55.23% | 9.07%–9.45% |
| Average delivery duration | 31.38 days | 10.88 days |

The negative-review order rate was approximately 5.84 times higher among late orders.

The difference in negative-review order rates was 44.86 percentage points.

Average review scores were 1.73 points lower among late orders.

Late orders took approximately 20.50 additional days to reach customers on average.

## 4. Statistical Testing

Three statistical tests were used to assess the observed differences.

| Test | Purpose | Result |
|---|---|---|
| Welch's independent t-test | Compare average order-level review scores | p < 0.001 |
| Two-proportion z-test | Compare negative-review order rates | p < 0.001 |
| Mann–Whitney U test | Compare order-level review-score distributions | p < 0.001 |

All three tests provide strong statistical evidence of differences between late and on-time orders.

The Mann–Whitney U test is particularly useful because review scores are ordinal and do not need to follow a normal distribution for this test.

Displayed p-values of zero from the software represent numerical underflow, not an exactly zero probability. Results are therefore reported as p < 0.001.

## 5. Key Business Insights

### 5.1 Late delivery is strongly associated with negative customer feedback

More than half of late orders had at least one negative review, compared with approximately 9% of on-time orders.

This indicates a substantial customer experience gap associated with delivery delays.

### 5.2 Delivery duration differs considerably

Late orders took an average of 31.38 days to reach customers, compared with 10.88 days for on-time orders.

This difference highlights the importance of monitoring delivery duration alongside promised delivery dates.

### 5.3 Delivery performance should be included in customer experience monitoring

Operational reporting should track:
- Late-delivery rate.
- Average and median delivery duration.
- Negative-review order rate.
- Average review score.
- Negative-review rate by seller, category, and delivery period.

### 5.4 Operational prioritization should consider customer impact

Delivery investigations should prioritize areas where late-delivery volume and negative customer feedback are both high.

This can help direct operational resources toward problems with greater potential customer impact.

## 6. Limitations

- The dataset is historical marketplace data covering 2016–2018.
- Statistical association does not establish that late delivery caused negative reviews.
- Product quality, seller behavior, logistics, customer expectations, and other factors may influence review scores.
- Multiple review records can belong to one order. The negative-review order rate counts each order once, while review-record rates use individual scored review records.
- Average order-level review scores can conceal variation among multiple reviews attached to an order.
- The statistical tests compare groups and do not control for potential confounding variables.
- Statistical significance does not, by itself, establish business causation.

## 7. Recommended Business Actions

1. Monitor negative-review rates alongside late-delivery rates.
2. Investigate periods, sellers, and categories with both high delay rates and poor customer feedback.
3. Review carrier performance and delivery geography before attributing delays to sellers.
4. Establish operational alerts for deteriorating delivery and customer experience indicators.
5. Consider a follow-up regression analysis to evaluate whether delivery delays remain associated with negative feedback after controlling for other available order characteristics.

## 8. Conclusion

The analysis identifies a substantial relationship between late delivery and poorer customer review outcomes.

Late orders have lower average review scores, higher negative-review rates, and substantially longer delivery durations.

These findings support treating delivery reliability as an important customer experience performance indicator. Further investigation is needed to isolate the contribution of delivery delays from other factors influencing customer satisfaction.