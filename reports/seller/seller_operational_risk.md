# Seller Operational Risk Analysis

## 1. Objective

Identify sellers with potentially elevated delivery risk by comparing their late-delivery performance against the overall eligible seller-association benchmark.

The analysis is intended to prioritize operational investigation, not establish that individual sellers caused delivery delays.

## 2. Methodology

- Analysis grain: seller-order association.
- Minimum eligibility threshold: 30 eligible associations per seller.
- Eligible sellers: 627.
- Eligible associations: 81,647.
- Late associations: 6,523.
- Weighted late-delivery benchmark: 7.99%.
- Statistical screening: Wilson 95% confidence intervals.
- Risk classification: a seller is flagged when the lower confidence bound of its late-delivery rate exceeds the overall benchmark.

The minimum sample threshold reduces instability among very small sellers. Wilson intervals account for uncertainty in each seller's observed late-delivery proportion.

## 3. Overall Findings

| Metric | Result |
|---|---:|
| Eligible sellers | 627 |
| Overall late-delivery benchmark | 7.99% |
| Sellers not statistically elevated | 541 |
| Sellers flagged as elevated | 86 |

The screening identified 86 sellers whose observed late-delivery performance was statistically elevated relative to the benchmark under the selected criterion.

These sellers should be treated as an investigation shortlist rather than confirmed operational failures.

## 4. High-Impact Sellers

The following sellers combine elevated delivery risk with comparatively high delivered revenue.

| Seller city | Eligible associations | Late associations | Late rate | Delivered revenue |
|---|---:|---:|---:|---:|
| Guariba, SP | 1,124 | 130 | 11.57% | R$226,987.93 |
| Ibitinga, SP | 1,772 | 195 | 11.00% | R$196,882.12 |
| Sumaré, SP | 578 | 59 | 10.21% | R$190,917.14 |
| Itaquaquecetuba, SP | 973 | 98 | 10.07% | R$186,570.05 |
| São Paulo, SP | 910 | 92 | 10.11% | R$138,208.56 |
| Petrópolis, RJ | 722 | 72 | 9.97% | R$112,461.50 |
| Ribeirão Preto, SP | 558 | 68 | 12.19% | R$112,436.18 |
| São José do Rio Preto, SP | 1,399 | 148 | 10.58% | R$106,655.71 |

## 5. Key Observations

1. **Risk and business impact should be considered together.** A seller with a high late-delivery percentage may have relatively few associations and low delivered revenue. High-volume sellers with elevated rates can represent a larger operational exposure.

2. **Ibitinga and Guariba deserve investigation priority.** Both have substantial association volumes, elevated late-delivery rates, and relatively high delivered revenue.

3. **The highest late-delivery percentage does not necessarily represent the greatest business impact.** Prioritization should consider sample size, excess late associations, and revenue exposure alongside the percentage.

4. **Seller location is not proof of seller responsibility.** Delivery outcomes may also be affected by carrier performance, geography, customer location, and other logistics factors.

## 6. Limitations

- Seller-order associations are not equivalent to unique marketplace orders.
- Order-level delivery timestamps attributed to seller associations do not establish seller causation.
- The 30-association minimum is a practical screening threshold, not a universal statistical standard.
- The analysis screens 627 sellers individually. Multiple comparisons can increase the probability of false-positive flags.
- Wilson intervals do not, by themselves, correct for multiple testing.
- The dataset is historical and represents marketplace activity from 2016–2018.

## 7. Recommended Business Actions

1. Prioritize investigation of high-volume sellers with elevated late-delivery rates.
2. Compare carrier allocation and destination geography before attributing delays to sellers.
3. Review order processing and dispatch timelines for the highest-impact sellers.
4. Monitor late-delivery rates and excess late associations over time.
5. Reassess flagged sellers using additional observation periods before taking corrective action.

## 8. Conclusion

The analysis provides a statistically informed way to screen seller delivery performance and prioritize operational investigation. Combining confidence intervals with association volume and revenue exposure produces a more useful shortlist than ranking sellers by late-delivery percentage alone.
