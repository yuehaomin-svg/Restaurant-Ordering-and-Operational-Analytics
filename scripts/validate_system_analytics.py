import json
from pathlib import Path

import pandas as pd

from app.database import SessionLocal
from app.routers.analytics import customer_repeat, daily_sales, hourly_demand, menu_engineering, sales_summary


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BI_DIR = PROJECT_ROOT / "data" / "processed" / "bi"


def json_default(value):
    if isinstance(value, dict):
        return {key: json_default(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_default(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value


def main() -> None:
    BI_DIR.mkdir(parents=True, exist_ok=True)
    database = SessionLocal()
    try:
        summary = sales_summary(None, None, database)
        products = menu_engineering(None, None, database)
        hourly = hourly_demand(None, None, database)
        repeat = customer_repeat(None, None, database)
        daily = daily_sales(None, None, database)
    finally:
        database.close()

    product_frame = pd.DataFrame(products)
    hourly_frame = pd.DataFrame(hourly)
    daily_frame = pd.DataFrame(daily)
    product_frame.to_csv(BI_DIR / "system_product_performance.csv", index=False)
    hourly_frame.to_csv(BI_DIR / "system_hourly_demand.csv", index=False)
    daily_frame.to_csv(BI_DIR / "system_daily_sales.csv", index=False)

    top_product = products[0]
    peak_hour = max(hourly, key=lambda item: item["orders"])
    segment_counts = pd.Series([item["menu_segment"] for item in products]).value_counts().to_dict()
    results = {
        "dataset": "Deterministic synthetic restaurant orders",
        "summary": summary,
        "top_product": top_product,
        "peak_hour": peak_hour,
        "customer_repeat": repeat,
        "menu_segments": segment_counts,
        "checks": {
            "net_sales_identity": summary["gross_sales"] - summary["refund_total"] == summary["net_sales"],
            "hourly_share_sum": round(sum(item["order_share"] for item in hourly), 4),
            "repeat_rate_valid": 0 <= repeat["repeat_customer_rate"] <= 1,
            "all_menu_segments_present": len(segment_counts) >= 1,
        },
    }
    (PROJECT_ROOT / "docs" / "system-analysis-results.json").write_text(
        json.dumps(json_default(results), indent=2), encoding="utf-8"
    )

    report = f"""# System Data Analysis

## Purpose

The deterministic restaurant dataset verifies that the operational database and analytical views can produce product metrics. Findings describe system feasibility and are not claims about a real restaurant.

## Pipeline Verification

- Gross sales: {summary['gross_sales']}.
- Refund amount: {summary['refund_total']}.
- Net sales: {summary['net_sales']}.
- Refund rate: {float(summary['refund_rate']) * 100:.2f}%.
- Net-sales identity check: {'passed' if results['checks']['net_sales_identity'] else 'failed'}.
- Hourly order-share total: {results['checks']['hourly_share_sum']}.
- Repeat-rate range check: {'passed' if results['checks']['repeat_rate_valid'] else 'failed'}.

## Product Engineering

The analytical view allocates order-level refunds to line items pro rata for product comparison only. The top net-sales item is {top_product['name']} in segment `{top_product['menu_segment']}`. Segment counts are `{segment_counts}`.

## Hourly Demand

Peak simulated demand occurs at {peak_hour['hour']}:00 with {peak_hour['orders']} orders and {float(peak_hour['order_share']) * 100:.2f}% of completed orders. This verifies that time-grouped operational demand is computable from `orders.placed_at`.

## Customer Repeat

- Identified customers: {repeat['identified_customers']}.
- Repeat-customer rate: {float(repeat['repeat_customer_rate']) * 100:.2f}%.
- Repeat-order rate: {float(repeat['repeat_order_rate']) * 100:.2f}%.
- Average orders per identified customer: {repeat['average_orders_per_customer']}.

The synthetic distribution is designed to exercise repeat calculations. Real behavioral validity is evaluated separately on UCI Online Retail II.

## Scope

- Transaction and concurrency correctness are tested separately.
- Performance is tested at 1,000, 10,000, and 50,000 orders.
- This analysis verifies metric computation and visualization readiness.
"""
    (PROJECT_ROOT / "docs" / "system-analysis.md").write_text(report, encoding="utf-8")
    print(json.dumps(json_default(results), indent=2))


if __name__ == "__main__":
    main()
