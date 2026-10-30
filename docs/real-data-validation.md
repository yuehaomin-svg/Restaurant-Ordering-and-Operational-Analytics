# Real Behavior Validation

## Purpose

UCI Online Retail II is used to validate whether the project's product-analysis methods remain computable and useful on real customer transaction behavior. It is not restaurant data, so the result validates analytical transferability rather than direct restaurant impact.

## Metric Mapping

| System concept | Real transaction field | Method |
| --- | --- | --- |
| Order | `order_id` | Distinct transaction identifier |
| Order item | one CSV row | Quantity and historical price |
| Customer | `customer_id` | Identified-customer analysis |
| Menu/product item | `product_code` | Product contribution analysis |
| Refund | negative quantity or credit order | Gross/refund/net sales |
| Order time | `invoice_date` | Date and business-hour analysis |

## Data Quality

- Source period: 2009-12-01 07:45:00 to 2011-12-09 12:50:00.
- Transaction lines: 1,067,371.
- Distinct orders: 53,628.
- Distinct products: 5,304.
- Identified customers: 5,942.
- Return rows are retained and reported separately; exact duplicate source rows are retained because separate invoice lines may be legitimate.

## Results

- Gross sales: £20,972,968.12.
- Refund amount: £1,685,717.57.
- Net sales: £19,287,250.55.
- Refund rate: 8.0%.
- Largest net-sales product: REGENCY CAKESTAND 3 TIER (`22423`), £327,813.65.
- Peak demand hour: 12:00 with 8,098 orders (15.1%).
- Repeat-customer rate: 75.4%.
- Repeat-order rate: 86.8%.
- Repeat-customer net sales: £16,254,643.57.

## Method Validation

- Net sales is reproducible as positive line sales minus return value.
- Product engineering can classify real products by units sold and net-sales contribution.
- Hourly demand can identify behavioral timing patterns without restaurant-specific fields.
- Customer repeat behavior can be measured whenever customer identifiers are present.
- Return analysis becomes more meaningful on real data because actual negative transactions exist.

## Interpretation Boundaries

- Online retail behavior is not equivalent to restaurant behavior.
- Customer IDs are anonymized and cannot support demographic conclusions.
- Product profitability cannot be measured because product costs are unavailable.
- Repeat analysis excludes rows without customer identifiers.
- The analysis is descriptive and does not establish causal campaign or pricing effects.
