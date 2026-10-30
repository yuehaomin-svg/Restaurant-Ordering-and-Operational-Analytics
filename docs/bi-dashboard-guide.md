# Power BI Dashboard Learning Guide

## Learning Goal

Build a small but credible BI product from the real transaction data. The goal is not to create many chart types. The goal is to model data, define measures, support filtering, and explain decisions clearly.

## Source Files

Use the generated files in `data/processed/bi`:

- `real_transaction_fact.csv`: invoice-line fact table.
- `real_product_performance.csv`: product measures and product-engineering segment.
- `real_customer_summary.csv`: customer order count and customer sales measures.
- `real_hourly_demand.csv`: hourly demand measures.
- `real_daily_sales.csv`: daily sales measures.

Start with `real_transaction_fact.csv`. Import the summary tables only when they simplify a visual or provide a dimension.

## Data Model

Recommended model:

```text
dim_date 1 ---- * real_transaction_fact
dim_product 1 ---- * real_transaction_fact
dim_customer 1 ---- * real_transaction_fact
```

In Power Query:

1. Load `real_transaction_fact.csv`.
2. Set `invoice_date` to Date/Time.
3. Set `order_date` to Date.
4. Set `business_hour` to Whole Number.
5. Set `quantity`, `unit_price`, `gross_sales`, `refund_amount`, and `net_sales` to Decimal Number.
6. Keep `order_id`, `customer_id`, and `product_code` as Text so leading zeros are preserved.
7. Create `dim_product` by keeping `product_code`, `product_name`, and `menu_segment`, then removing duplicates.
8. Create `dim_customer` from `real_customer_summary.csv`.
9. Create `dim_date` with `CALENDAR(MIN('real_transaction_fact'[order_date]), MAX('real_transaction_fact'[order_date]))`.
10. Add Month, Month Number, Weekday, Weekday Number, and Is Weekend columns to `dim_date`.

Do not import Excel as the final BI source after cleaning; use the generated CSV so the data preparation is reproducible.

## Core Measures

Create one measure table named `Metrics` and define:

```DAX
Gross Sales = SUM('real_transaction_fact'[gross_sales])
```

```DAX
Refund Amount = SUM('real_transaction_fact'[refund_amount])
```

```DAX
Net Sales = [Gross Sales] - [Refund Amount]
```

```DAX
Refund Rate = DIVIDE([Refund Amount], [Gross Sales])
```

```DAX
Orders = DISTINCTCOUNT('real_transaction_fact'[order_id])
```

```DAX
Average Order Value = DIVIDE([Gross Sales], [Orders])
```

```DAX
Transaction Lines = COUNTROWS('real_transaction_fact')
```

Use `DIVIDE` rather than division so blank and zero totals do not create errors.

## Page 1: Executive Overview

Visuals:

- Cards: Gross Sales, Net Sales, Refund Amount, Refund Rate, Orders.
- Line chart: Net Sales by `dim_date[Date]`.
- Bar chart: Net Sales by Month.
- Small table: Refund Amount and Refund Rate by Country.
- Slicer: Date Range.

The page should answer:

> What is the scale, trend, and refund exposure of the business?

## Page 2: Product Strategy

Visuals:

- Scatter chart: `units_sold` on X, `net_sales` on Y, `product_code` as legend/details, `menu_segment` as legend.
- Bar chart: top ten products by Net Sales.
- Matrix: `menu_segment` versus product count, units sold, and net sales.
- Slicer: `menu_segment`.

Add data-point tooltips containing product name, orders, units sold, refunds, and net sales.

The page should answer:

> Which products create value, which create volume, and which need review?

## Page 3: Customer Growth

Visuals:

- Cards: Identified Customers, Repeat Customer Rate, Repeat Order Rate, Orders per Customer.
- Column chart: customer count by frequency band.
- Bar chart: Net Sales by customer frequency band.
- Table: top customers by Net Sales with Order Count and Refund Amount.
- Slicer: Customer Frequency Band.

The page should answer:

> How much value depends on repeat behavior, and how concentrated is it?

## Page 4: Timing and Operations

Visuals:

- Column chart: Orders by `business_hour`.
- Line chart: Net Sales by `business_hour`.
- Matrix: Weekday versus business hour, using Orders as values.
- Line chart: Refund Rate by Month.
- Slicers: Date, Weekday, Country.

The page should answer:

> When does demand concentrate, and where do quality problems appear?

## Design Rules

- Use a maximum of two accent colors plus neutral colors.
- Keep KPI cards at the top of each page.
- Sort product bars by Net Sales descending.
- Format currency without unnecessary decimal places.
- Format refund rate as `0.0%`.
- Turn off visual headers that do not add information.
- Keep one primary question per page.
- Use titles and subtitles to explain the decision, not the chart type.
- Add tooltips that explain the metric definition.
- Test each slicer with at least two different date ranges.

## Suggested Measure Tests

- Net Sales must equal Gross Sales minus Refund Amount.
- Orders cannot exceed Transaction Lines.
- Sum of hourly Orders must equal total Orders when no filter excludes a transaction.
- Repeat Customer Rate must remain between 0% and 100%.
- Product units must not become negative after returns are separated.
- Refund Rate must be blank rather than an error when Gross Sales is zero.

## Four Practice Exercises

### Exercise 1: Data Model

Build the fact, product, customer, and date tables. Verify that filters propagate from `dim_date` to the fact table.

### Exercise 2: DAX Metrics

Create the core measures in a measure table. Add one visual card for each and verify it changes with the date slicer.

### Exercise 3: Product Analysis

Build the product scatter chart and explain the four product segments in a short visual subtitle.

### Exercise 4: Decision Narrative

Write one observation and one recommendation for each page. Replace generic chart titles with decision-oriented titles.

Example:

```text
Wrong: Hourly Orders
Better: Demand concentrates at midday; review staffing and preparation capacity
```

## Deliverables

- One Power BI `.pbix` file.
- Four PDF pages or high-resolution screenshots.
- A one-page metric definition sheet.
- A short README explaining the source, cleaning, data model, and refresh steps.
- Three decision insights with evidence and limitations.

Do not commit raw UCI data to Git. Commit the data-preparation scripts and optionally a small sample file so another group member can reproduce the model.
