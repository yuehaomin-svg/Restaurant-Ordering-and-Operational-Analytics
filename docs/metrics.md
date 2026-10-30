# Metric Dictionary

## Common Principles

- Gross sales, refund amount, and net sales are always separate.
- Open and cancelled orders are excluded from completed-sales metrics.
- Date filters use restaurant-local `order_date` and include both start and end dates.
- Historical line prices are used instead of current menu/product prices.
- Identified-customer metrics exclude rows without a customer identifier.
- Synthetic restaurant results demonstrate system feasibility; UCI real-data results demonstrate analytical transferability.

## Gross Sales

- Definition: sum of completed order totals before refunds.
- System source: `v_order_financials.gross_sales`.
- Real-data source: positive transaction-line value.
- Grain: selected reporting period.
- Why it matters: total completed transaction value.

## Refund Amount

- Definition: recorded refunds or returned transaction value.
- System source: order-level refunds linked through payments.
- Real-data source: absolute value of negative transaction lines.
- Grain: selected reporting period.
- Reporting rule: never subtract refunds silently from gross sales.

## Net Sales

- Definition: gross sales minus refund amount.
- Formula: `net_sales = gross_sales - refund_amount`.
- System source: `v_order_financials.net_sales`.
- Real-data source: positive line value minus negative line value.
- Why it matters: retained sales value after returns and service corrections.

## Refund Rate

- Definition: refund amount divided by gross sales.
- Formula: `refund_rate = refund_amount / gross_sales`.
- Display: percentage to one decimal place.
- Interpretation: financial leakage and potential quality/service risk.

## Average Order Value

- Definition: gross completed sales divided by completed orders.
- Formula: `gross_sales / completed_orders`.
- Open and cancelled orders are excluded.

## Product Units Sold

- Definition: positive product quantities in completed transaction lines.
- System source: positive quantities in `order_items`.
- Real-data source: positive quantities in UCI transaction lines.
- Returns are reported separately so demand is not hidden by net quantity.

## Product Net Sales

- System definition: gross line value adjusted by the order-level refund ratio.
- Formula: `line_total * (1 - refund_amount / gross_sales)`.
- Purpose: comparable product-level analysis only; it is not an accounting allocation.
- Real-data definition: positive line value minus negative return value for the same product.

## Menu/Product Engineering Segment

The analysis compares two dimensions:

- Demand: product units sold relative to the average product units sold.
- Sales value: product net sales relative to average product net sales.

Segments:

| Demand | Net sales | Segment | Recommended response |
| --- | --- | --- | --- |
| High | High | Stars | Keep prominent; test premium variants |
| High | Low | Plowhorses | Protect availability; improve bundling/upsell |
| Low | High | Puzzles | Improve placement and targeted discovery |
| Low | Low | Dogs | Review recipe, price, visibility, or replacement |

This is sales-contribution analysis, not menu engineering by profit contribution, because product cost is unavailable.

## Hourly Demand

- Definition: distinct completed orders grouped by transaction hour.
- Additional measures: gross sales, refund amount, net sales, and order share.
- System source: `orders.placed_at`.
- Real-data source: `invoice_date`.
- Why it matters: staffing, capacity, preparation, and campaign timing.

## Identified Customers

- Definition: distinct customers with a non-null customer identifier.
- Anonymous transaction rows are excluded from repeat metrics.

## Repeat Customer Rate

- Definition: identified customers with more than one order divided by all identified customers in the selected period.
- Formula: `repeat_customers / identified_customers`.
- Scope: repeat behavior within the selected date window.

## Repeat Order Rate

- Definition: additional orders after each customer's first order, divided by all identified orders.
- Formula: `sum(order_count - 1 for repeat customers) / identified_orders`.
- Interpretation: dependence on repeat transaction behavior.

## Customer Frequency Bands

- `1 order`: one-time customers in the period.
- `2-3 orders`: occasional repeat customers.
- `4-10 orders`: regular repeat customers.
- `11+ orders`: high-frequency customers.

## Real Dataset Mapping

| System concept | UCI Online Retail II | Validation method |
| --- | --- | --- |
| Order | `order_id` | Order and time aggregation |
| Order item | one transaction row | Product demand and basket grain |
| Menu item | `product_code` | Product engineering |
| Customer | `customer_id` | Repeat and frequency analysis |
| Price | `unit_price` | Historical line value |
| Refund | negative quantity/credit order | Gross/refund/net sales |
| Order time | `invoice_date` | Hour and date analysis |

## Governance Rules

- Every dashboard measure must map to one definition in this document.
- Net-sales calculations must satisfy `gross - refund = net`.
- Product-level system refunds are analytical allocations only.
- Repeat metrics must state whether they are all-time or selected-period measures.
- Real-data findings must include the domain-transfer limitation.
- No profit or causal claims are allowed without cost data or experimental design.
