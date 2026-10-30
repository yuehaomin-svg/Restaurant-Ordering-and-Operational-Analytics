# Analysis Method Validation

## Validation Question

Can the restaurant system's analytical layer compute the same core product methods on real transaction behavior and produce useful decision information?

## Test Design

Two datasets are evaluated with the same conceptual methods:

1. Deterministic restaurant transactions verify the system pipeline and database views.
2. UCI Online Retail II verifies product, time, customer, and refund analysis on real behavior.

| Method | System result | Real-data result | Validation |
| --- | --- | --- | --- |
| Gross/refund/net sales | Net-sales identity passed | £20.97m gross, £1.69m refunds, £19.29m net | Valid |
| Product engineering | 10 items across four segments | 5,304 products across four segments | Valid |
| Hourly demand | 19:00 simulated peak, 21.7% of orders | 12:00 real peak, 15.1% of orders | Valid |
| Repeat customer rate | 73.6% on synthetic behavior | 75.4% on identified real customers | Valid |
| Repeat order rate | 74.2% on synthetic behavior | 86.8% on identified real orders | Valid |
| Refund analysis | 4.0% refund rate | 8.0% refund rate | Valid |

## Supported Conclusions

- The system's analytical views can compute the core methods from transaction-level fields.
- Product demand and sales contribution can be analyzed without restaurant-specific fields.
- Hourly behavior analysis transfers directly from order timestamps.
- Repeat behavior is computable whenever customers are identified.
- Real return records significantly strengthen refund and product-quality analysis.
- The same BI model can support both datasets after applying documented field mappings.

## Unsupported Conclusions

- The real dataset does not prove that a restaurant would achieve similar metrics.
- It does not validate table turnover or seating efficiency.
- It does not prove pricing or campaign causality.
- It cannot measure profitability without product costs.
- Repeat rates are conditional on identified customer IDs and the selected period.

## Result

The analytical method is feasible and transferable for order, product, time, customer, and refund analysis. Restaurant-specific operational measures still require restaurant data, especially table sessions, preparation duration, staffing, and seat capacity.
