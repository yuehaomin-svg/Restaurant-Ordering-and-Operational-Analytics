# Portfolio Presentation Notes

## Recommended Story

1. Start with the business process: menu, table, order, checkout and refund.
2. Explain why transaction history is preserved instead of deleting refunded sales.
3. Show the metric layer and the three SQL analytical views.
4. Use the synthetic restaurant data to demonstrate system correctness.
5. Use UCI Online Retail II only to validate that the same product, customer, refund and timing methods operate on real behavior.
6. Close with testing, concurrency, scale and query-optimization evidence.

## Suggested Resume Bullets

- Built a MySQL and FastAPI restaurant transaction platform covering ordering, checkout, refunds and operational analytics, with 10 normalized business tables and 3 analytical views.
- Defined product, customer, refund and hourly-demand metrics and validated the framework on 1.07 million real retail transaction lines.
- Tested transaction integrity, concurrent table usage and 1K/10K/50K data volumes, using indexes and `EXPLAIN` plans to support query-performance decisions.

## Interview Boundaries

- The UCI dataset validates analytical behavior; it does not prove restaurant business results.
- The menu-engineering view measures sales contribution, not profitability, because product cost is unavailable.
- Repeat metrics exclude anonymous transactions without customer identifiers.
- A public deployment would require authentication and access controls before exposing mutation endpoints.
