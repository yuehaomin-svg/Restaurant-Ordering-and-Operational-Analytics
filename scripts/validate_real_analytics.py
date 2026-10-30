import json
from pathlib import Path

import pandas as pd

from scripts.generate_report_charts import horizontal_bars, vertical_bars


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FACT_PATH = PROJECT_ROOT / "data" / "processed" / "real_transaction_fact.csv"
BI_DIR = PROJECT_ROOT / "data" / "processed" / "bi"
RESULTS_PATH = PROJECT_ROOT / "docs" / "real-data-results.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "real-data-validation.md"


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def money(value: float) -> str:
    return f"£{value:,.2f}"


def main() -> None:
    fact = pd.read_csv(
        FACT_PATH,
        dtype={
            "order_id": "string",
            "customer_id": "string",
            "product_code": "string",
            "product_name": "string",
            "country": "string",
        },
        parse_dates=["invoice_date"],
    )
    BI_DIR.mkdir(parents=True, exist_ok=True)

    gross_sales = float(fact["gross_sales"].sum())
    refund_amount = float(fact["refund_amount"].sum())
    net_sales = float(fact["net_sales"].sum())
    order_count = int(fact["order_id"].nunique())

    product = fact.groupby("product_code", dropna=False, as_index=False).agg(
        product_name=("product_name", "first"),
        units_sold=("quantity", lambda values: int(values[values > 0].sum())),
        return_units=("quantity", lambda values: int(-values[values < 0].sum())),
        order_count=("order_id", "nunique"),
        gross_sales=("gross_sales", "sum"),
        refund_amount=("refund_amount", "sum"),
        net_sales=("net_sales", "sum"),
    )
    average_units = float(product["units_sold"].mean())
    average_net_sales = float(product["net_sales"].mean())
    product["menu_segment"] = "Dogs"
    product.loc[
        (product["units_sold"] >= average_units) & (product["net_sales"] < average_net_sales), "menu_segment"
    ] = "Plowhorses"
    product.loc[
        (product["units_sold"] < average_units) & (product["net_sales"] >= average_net_sales), "menu_segment"
    ] = "Puzzles"
    product.loc[
        (product["units_sold"] >= average_units) & (product["net_sales"] >= average_net_sales), "menu_segment"
    ] = "Stars"
    product = product.sort_values("net_sales", ascending=False)

    hourly = fact.groupby("business_hour", as_index=False).agg(
        order_count=("order_id", "nunique"),
        gross_sales=("gross_sales", "sum"),
        refund_amount=("refund_amount", "sum"),
        net_sales=("net_sales", "sum"),
    )
    hourly["order_share"] = hourly["order_count"] / max(order_count, 1)
    hourly = hourly.sort_values("business_hour")

    customer_rows = fact[fact["customer_id"].notna()]
    customer = customer_rows.groupby("customer_id", as_index=False).agg(
        order_count=("order_id", "nunique"),
        gross_sales=("gross_sales", "sum"),
        refund_amount=("refund_amount", "sum"),
        net_sales=("net_sales", "sum"),
    )
    identified_customers = int(len(customer))
    repeat_customers = int((customer["order_count"] > 1).sum())
    identified_orders = int(customer_rows["order_id"].nunique())
    repeat_orders = int((customer.loc[customer["order_count"] > 1, "order_count"] - 1).sum())
    repeat_customer_net_sales = float(customer.loc[customer["order_count"] > 1, "net_sales"].sum())
    frequency = pd.cut(
        customer["order_count"],
        bins=[0, 1, 3, 10, float("inf")],
        labels=["1 order", "2-3 orders", "4-10 orders", "11+ orders"],
    ).value_counts(sort=False)

    daily = fact.groupby("order_date", as_index=False).agg(
        order_count=("order_id", "nunique"),
        gross_sales=("gross_sales", "sum"),
        refund_amount=("refund_amount", "sum"),
        net_sales=("net_sales", "sum"),
    ).sort_values("order_date")

    product.to_csv(BI_DIR / "real_product_performance.csv", index=False)
    hourly.to_csv(BI_DIR / "real_hourly_demand.csv", index=False)
    customer.to_csv(BI_DIR / "real_customer_summary.csv", index=False)
    daily.to_csv(BI_DIR / "real_daily_sales.csv", index=False)

    top_product = product.iloc[0]
    peak_hour = hourly.sort_values("order_count", ascending=False).iloc[0]
    results = {
        "dataset": "UCI Online Retail II",
        "date_min": str(fact["invoice_date"].min()),
        "date_max": str(fact["invoice_date"].max()),
        "order_count": order_count,
        "transaction_lines": int(len(fact)),
        "product_count": int(fact["product_code"].nunique()),
        "identified_customers": identified_customers,
        "gross_sales": round(gross_sales, 2),
        "refund_amount": round(refund_amount, 2),
        "net_sales": round(net_sales, 2),
        "refund_rate": round(refund_amount / gross_sales, 4),
        "top_product": {
            "product_code": top_product["product_code"],
            "product_name": top_product["product_name"],
            "net_sales": round(float(top_product["net_sales"]), 2),
        },
        "peak_hour": {
            "business_hour": int(peak_hour["business_hour"]),
            "order_count": int(peak_hour["order_count"]),
            "order_share": round(float(peak_hour["order_share"]), 4),
        },
        "customer_repeat": {
            "repeat_customers": repeat_customers,
            "repeat_customer_rate": round(repeat_customers / identified_customers, 4),
            "identified_orders": identified_orders,
            "repeat_orders": repeat_orders,
            "repeat_order_rate": round(repeat_orders / identified_orders, 4),
            "repeat_customer_net_sales": round(repeat_customer_net_sales, 2),
            "frequency_distribution": {str(label): int(count) for label, count in frequency.items()},
        },
        "menu_segments": product["menu_segment"].value_counts().to_dict(),
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    horizontal_bars(
        "Real transaction product performance (top 10 by net sales)",
        "real_product_performance.svg",
        [(f"{row.product_code} · {row.product_name}", float(row.net_sales)) for row in product.head(10).itertuples()],
    )
    vertical_bars(
        "Real transaction hourly demand",
        "real_hourly_demand.svg",
        [(str(int(row.business_hour)), float(row.order_count)) for row in hourly.itertuples()],
    )
    horizontal_bars(
        "Real transaction customer frequency bands",
        "real_customer_frequency.svg",
        [(str(label), float(count)) for label, count in frequency.items()],
    )

    report = f"""# Real Behavior Validation

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

- Source period: {results['date_min']} to {results['date_max']}.
- Transaction lines: {results['transaction_lines']:,}.
- Distinct orders: {results['order_count']:,}.
- Distinct products: {results['product_count']:,}.
- Identified customers: {identified_customers:,}.
- Return rows are retained and reported separately; exact duplicate source rows are retained because separate invoice lines may be legitimate.

## Results

- Gross sales: {money(gross_sales)}.
- Refund amount: {money(refund_amount)}.
- Net sales: {money(net_sales)}.
- Refund rate: {percent(results['refund_rate'])}.
- Largest net-sales product: {results['top_product']['product_name']} (`{results['top_product']['product_code']}`), {money(results['top_product']['net_sales'])}.
- Peak demand hour: {results['peak_hour']['business_hour']}:00 with {results['peak_hour']['order_count']:,} orders ({percent(results['peak_hour']['order_share'])}).
- Repeat-customer rate: {percent(results['customer_repeat']['repeat_customer_rate'])}.
- Repeat-order rate: {percent(results['customer_repeat']['repeat_order_rate'])}.
- Repeat-customer net sales: {money(repeat_customer_net_sales)}.

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
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
