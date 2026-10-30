from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def period_filter(start_at: date | None, end_at: date | None) -> tuple[str, dict]:
    clauses = []
    parameters = {}
    if start_at:
        clauses.append("order_date >= :start_at")
        parameters["start_at"] = start_at
    if end_at:
        clauses.append("order_date <= :end_at")
        parameters["end_at"] = end_at
    return (" AND " + " AND ".join(clauses) if clauses else ""), parameters


def item_period_filter(start_at: date | None, end_at: date | None) -> tuple[str, dict]:
    clauses = []
    parameters = {}
    if start_at:
        clauses.append("sales.order_date >= :start_at")
        parameters["start_at"] = start_at
    if end_at:
        clauses.append("sales.order_date <= :end_at")
        parameters["end_at"] = end_at
    return (" AND " + " AND ".join(clauses) if clauses else ""), parameters


@router.get("/summary")
def sales_summary(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> dict:
    where_clause, parameters = period_filter(start_at, end_at)
    row = database.execute(text(f"""
        SELECT COUNT(*) AS order_count,
               COALESCE(SUM(gross_sales), 0.00) AS gross_sales,
               COALESCE(SUM(refund_amount), 0.00) AS refund_total,
               COALESCE(SUM(net_sales), 0.00) AS net_sales,
               COALESCE(AVG(gross_sales), 0.00) AS average_order_value
        FROM v_order_financials
        WHERE 1 = 1 {where_clause}
    """), parameters).one()
    gross_sales = Decimal(row.gross_sales).quantize(Decimal("0.01"))
    refund_total = Decimal(row.refund_total).quantize(Decimal("0.01"))
    net_sales = Decimal(row.net_sales).quantize(Decimal("0.01"))
    refund_rate = (refund_total / gross_sales) if gross_sales else Decimal("0.00")
    return {
        "order_count": row.order_count,
        "gross_sales": gross_sales,
        "revenue": gross_sales,
        "refund_total": refund_total,
        "net_sales": net_sales,
        "average_order_value": Decimal(row.average_order_value).quantize(Decimal("0.01")),
        "refund_rate": refund_rate.quantize(Decimal("0.0001")),
    }


@router.get("/daily-sales")
def daily_sales(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> list[dict]:
    where_clause, parameters = period_filter(start_at, end_at)
    rows = database.execute(text(f"""
        SELECT order_date,
               COUNT(*) AS order_count,
               SUM(gross_sales) AS gross_sales,
               SUM(refund_amount) AS refund_total,
               SUM(net_sales) AS net_sales
        FROM v_order_financials
        WHERE 1 = 1 {where_clause}
        GROUP BY order_date
        ORDER BY order_date
    """), parameters)
    return [
        {
            "order_date": row.order_date.isoformat(),
            "order_count": row.order_count,
            "gross_sales": row.gross_sales,
            "refund_total": row.refund_total,
            "net_sales": row.net_sales,
        }
        for row in rows
    ]


@router.get("/menu-performance")
def menu_performance(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> list[dict]:
    where_clause, parameters = item_period_filter(start_at, end_at)
    rows = database.execute(text(f"""
        SELECT menu_items.id AS menu_item_id,
               menu_items.name,
               SUM(sales.quantity) AS quantity,
               SUM(sales.gross_item_sales) AS sales,
               SUM(sales.net_item_sales) AS net_sales
        FROM v_order_item_sales AS sales
        JOIN menu_items ON menu_items.id = sales.menu_item_id
        WHERE 1 = 1 {where_clause}
        GROUP BY menu_items.id, menu_items.name
        ORDER BY net_sales DESC
    """), parameters)
    return [
        {
            "menu_item_id": row.menu_item_id,
            "name": row.name,
            "quantity": row.quantity,
            "sales": row.sales,
            "net_sales": row.net_sales,
        }
        for row in rows
    ]


@router.get("/menu-engineering")
def menu_engineering(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> list[dict]:
    where_clause, parameters = item_period_filter(start_at, end_at)
    rows = database.execute(text(f"""
        WITH item_stats AS (
            SELECT menu_items.id AS menu_item_id,
                   menu_items.name,
                   menu_categories.name AS category_name,
                   SUM(sales.quantity) AS quantity,
                   SUM(sales.gross_item_sales) AS gross_sales,
                   SUM(sales.net_item_sales) AS net_sales,
                   COUNT(DISTINCT sales.order_id) AS order_count
            FROM v_order_item_sales AS sales
            JOIN menu_items ON menu_items.id = sales.menu_item_id
            LEFT JOIN menu_categories ON menu_categories.id = menu_items.category_id
            WHERE 1 = 1 {where_clause}
            GROUP BY menu_items.id, menu_items.name, menu_categories.name
        ), thresholds AS (
            SELECT AVG(quantity) AS average_quantity, AVG(net_sales) AS average_net_sales
            FROM item_stats
        )
        SELECT item_stats.*,
               thresholds.average_quantity,
               thresholds.average_net_sales,
               CASE
                   WHEN item_stats.quantity >= thresholds.average_quantity AND item_stats.net_sales >= thresholds.average_net_sales THEN 'Stars'
                   WHEN item_stats.quantity >= thresholds.average_quantity AND item_stats.net_sales < thresholds.average_net_sales THEN 'Plowhorses'
                   WHEN item_stats.quantity < thresholds.average_quantity AND item_stats.net_sales >= thresholds.average_net_sales THEN 'Puzzles'
                   ELSE 'Dogs'
               END AS menu_segment
        FROM item_stats
        CROSS JOIN thresholds
        ORDER BY item_stats.net_sales DESC
    """), parameters)
    recommendations = {
        "Stars": "Keep prominent and test incremental price or premium variants.",
        "Plowhorses": "Protect availability and improve bundling or upsell value.",
        "Puzzles": "Improve menu placement and run targeted discovery campaigns.",
        "Dogs": "Review recipe, price, visibility, or replacement opportunities.",
    }
    return [
        {
            "menu_item_id": row.menu_item_id,
            "name": row.name,
            "category_name": row.category_name,
            "quantity": row.quantity,
            "order_count": row.order_count,
            "gross_sales": row.gross_sales,
            "net_sales": row.net_sales,
            "menu_segment": row.menu_segment,
            "recommendation": recommendations[row.menu_segment],
        }
        for row in rows
    ]


@router.get("/hourly-demand")
def hourly_demand(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> list[dict]:
    where_clause, parameters = period_filter(start_at, end_at)
    rows = database.execute(text(f"""
        SELECT business_hour,
               COUNT(*) AS orders,
               SUM(gross_sales) AS gross_sales,
               SUM(refund_amount) AS refund_total,
               SUM(net_sales) AS net_sales
        FROM v_order_financials
        WHERE 1 = 1 {where_clause}
        GROUP BY business_hour
        ORDER BY business_hour
    """), parameters).fetchall()
    total_orders = sum(row.orders for row in rows) or 1
    return [
        {
            "hour": row.business_hour,
            "orders": row.orders,
            "order_share": round(row.orders / total_orders, 4),
            "gross_sales": row.gross_sales,
            "refund_total": row.refund_total,
            "net_sales": row.net_sales,
        }
        for row in rows
    ]


@router.get("/customer-repeat")
def customer_repeat(
    start_at: date | None = Query(default=None),
    end_at: date | None = Query(default=None),
    database: Session = Depends(get_db),
) -> dict:
    where_clause, parameters = period_filter(start_at, end_at)
    summary = database.execute(text(f"""
        WITH customer_stats AS (
            SELECT customer_id,
                   COUNT(*) AS order_count,
                   SUM(net_sales) AS net_sales
            FROM v_order_financials
            WHERE customer_id IS NOT NULL {where_clause}
            GROUP BY customer_id
        )
        SELECT COUNT(*) AS identified_customers,
               COALESCE(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END), 0) AS repeat_customers,
               COALESCE(SUM(order_count), 0) AS identified_orders,
               COALESCE(SUM(CASE WHEN order_count > 1 THEN order_count - 1 ELSE 0 END), 0) AS repeat_orders,
               COALESCE(SUM(CASE WHEN order_count > 1 THEN net_sales ELSE 0 END), 0.00) AS repeat_customer_net_sales,
               COALESCE(AVG(order_count), 0) AS average_orders_per_customer
        FROM customer_stats
    """), parameters).one()
    distribution_rows = database.execute(text(f"""
        WITH customer_stats AS (
            SELECT customer_id, COUNT(*) AS order_count
            FROM v_order_financials
            WHERE customer_id IS NOT NULL {where_clause}
            GROUP BY customer_id
        )
        SELECT CASE
                   WHEN order_count = 1 THEN '1 order'
                   WHEN order_count BETWEEN 2 AND 3 THEN '2-3 orders'
                   ELSE '4+ orders'
               END AS frequency_band,
               COUNT(*) AS customer_count
        FROM customer_stats
        GROUP BY frequency_band
    """), parameters).fetchall()
    identified_customers = summary.identified_customers
    identified_orders = summary.identified_orders
    return {
        "identified_customers": identified_customers,
        "repeat_customers": summary.repeat_customers,
        "repeat_customer_rate": round(summary.repeat_customers / identified_customers, 4) if identified_customers else 0,
        "identified_orders": identified_orders,
        "repeat_orders": summary.repeat_orders,
        "repeat_order_rate": round(summary.repeat_orders / identified_orders, 4) if identified_orders else 0,
        "repeat_customer_net_sales": summary.repeat_customer_net_sales,
        "average_orders_per_customer": round(summary.average_orders_per_customer, 2),
        "frequency_distribution": [
            {"frequency_band": row.frequency_band, "customer_count": row.customer_count}
            for row in distribution_rows
        ],
    }
