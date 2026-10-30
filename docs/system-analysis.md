# System Data Analysis

## Purpose

The deterministic restaurant dataset verifies that the operational database and analytical views can produce product metrics. Findings describe system feasibility and are not claims about a real restaurant.

## Pipeline Verification

- Gross sales: 340957.00.
- Refund amount: 13705.00.
- Net sales: 327252.00.
- Refund rate: 4.02%.
- Net-sales identity check: passed.
- Hourly order-share total: 1.0.
- Repeat-rate range check: passed.

## Product Engineering

The analytical view allocates order-level refunds to line items pro rata for product comparison only. The top net-sales item is Seafood Pasta in segment `Stars`. Segment counts are `{'Dogs': 4, 'Stars': 3, 'Plowhorses': 2, 'Puzzles': 1}`.

## Hourly Demand

Peak simulated demand occurs at 19:00 with 217 orders and 21.70% of completed orders. This verifies that time-grouped operational demand is computable from `orders.placed_at`.

## Customer Repeat

- Identified customers: 155.
- Repeat-customer rate: 73.55%.
- Repeat-order rate: 74.21%.
- Average orders per identified customer: 3.88.

The synthetic distribution is designed to exercise repeat calculations. Real behavioral validity is evaluated separately on UCI Online Retail II.

## Scope

- Transaction and concurrency correctness are tested separately.
- Performance is tested at 1,000, 10,000, and 50,000 orders.
- This analysis verifies metric computation and visualization readiness.
