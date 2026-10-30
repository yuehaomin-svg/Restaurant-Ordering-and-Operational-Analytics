import csv
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from scripts.seed_data import seed_orders


SCALE_SIZES = [1_000, 10_000, 50_000]
INDEX_MODES = ["without_optional_indexes", "with_optional_indexes"]
ITERATIONS = 7
RESULTS_DIR = Path(__file__).resolve().parent.parent / "docs"


QUERIES = {
    "daily_sales": """
        SELECT DATE(placed_at) AS sales_date,
               COUNT(*) AS order_count,
               SUM(total_amount) AS revenue
        FROM orders
        WHERE status IN ('paid', 'partially_refunded', 'refunded')
          AND placed_at >= :start_at
          AND placed_at < :end_at
        GROUP BY DATE(placed_at)
        ORDER BY sales_date
    """,
    "menu_performance": """
        SELECT menu_items.id,
               menu_items.name,
               SUM(order_items.quantity) AS quantity,
               SUM(order_items.line_total) AS sales
        FROM order_items
        JOIN menu_items ON menu_items.id = order_items.menu_item_id
        JOIN orders ON orders.id = order_items.order_id
        WHERE orders.status IN ('paid', 'partially_refunded', 'refunded')
          AND orders.placed_at >= :start_at
          AND orders.placed_at < :end_at
        GROUP BY menu_items.id, menu_items.name
        ORDER BY sales DESC
    """,
    "hourly_demand": """
        SELECT HOUR(placed_at) AS business_hour,
               COUNT(*) AS order_count,
               SUM(total_amount) AS sales
        FROM orders
        WHERE status IN ('paid', 'partially_refunded', 'refunded')
          AND placed_at >= :start_at
          AND placed_at < :end_at
        GROUP BY HOUR(placed_at)
        ORDER BY business_hour
    """,
    "recent_orders": """
        SELECT order_no, total_amount, placed_at
        FROM orders
        WHERE status IN ('paid', 'partially_refunded', 'refunded')
        ORDER BY placed_at DESC
        LIMIT 50
    """,
    "customer_frequency": """
        SELECT customer_id,
               COUNT(*) AS order_count,
               SUM(total_amount) AS customer_sales
        FROM orders
        WHERE customer_id IS NOT NULL
          AND status IN ('paid', 'partially_refunded', 'refunded')
          AND placed_at >= :start_at
          AND placed_at < :end_at
        GROUP BY customer_id
        ORDER BY order_count DESC
        LIMIT 50
    """,
}


def index_exists(database, table_name: str, index_name: str) -> bool:
    if table_name == "orders":
        row = database.execute(text("SHOW INDEX FROM orders WHERE Key_name = :index_name"), {"index_name": index_name}).first()
    else:
        row = database.execute(text("SHOW INDEX FROM order_items WHERE Key_name = :index_name"), {"index_name": index_name}).first()
    return row is not None


def set_candidate_indexes(database, enabled: bool) -> None:
    actions = {
        "ix_orders_status_placed_at": ("orders", "status, placed_at"),
        "ix_orders_customer_placed_at": ("orders", "customer_id, placed_at"),
    }
    for index_name, (table_name, columns) in actions.items():
        exists = index_exists(database, table_name, index_name)
        if enabled and not exists:
            database.execute(text(f"CREATE INDEX {index_name} ON {table_name} ({columns})"))
        elif not enabled and exists:
            database.execute(text(f"DROP INDEX {index_name} ON {table_name}"))
    database.commit()


def benchmark_query(database, query: str) -> dict:
    parameters = {
        "start_at": datetime.now() - timedelta(days=40),
        "end_at": datetime.now() + timedelta(days=1),
    }
    first_rows = database.execute(text(query), parameters).fetchall()
    durations = []
    for _ in range(ITERATIONS):
        started_at = time.perf_counter()
        rows = database.execute(text(query), parameters).fetchall()
        durations.append((time.perf_counter() - started_at) * 1000)
    return {
        "median_ms": round(median(durations), 3),
        "min_ms": round(min(durations), 3),
        "max_ms": round(max(durations), 3),
        "result_rows": len(first_rows) if first_rows is not None else len(rows),
    }


def recreate_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def write_results(results: list[dict]) -> None:
    json_path = RESULTS_DIR / "evaluation_results.json"
    csv_path = RESULTS_DIR / "evaluation_results.csv"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    results = []
    try:
        for scale_size in SCALE_SIZES:
            recreate_database()
            database = SessionLocal()
            try:
                seed_orders(database, scale_size, random.Random(5003))
                database.commit()
                for index_mode in INDEX_MODES:
                    set_candidate_indexes(database, index_mode == "with_optional_indexes")
                    for query_name, query in QUERIES.items():
                        measurement = benchmark_query(database, query)
                        results.append({
                            "scale_size": scale_size,
                            "index_mode": index_mode,
                            "query_name": query_name,
                            **measurement,
                        })
                        print(scale_size, index_mode, query_name, measurement["median_ms"], flush=True)
            finally:
                database.close()
    finally:
        recreate_database()
        database = SessionLocal()
        try:
            seed_orders(database, 1_000, random.Random(5003))
            set_candidate_indexes(database, True)
            database.commit()
        finally:
            database.close()
    write_results(results)
    print(f"Wrote {len(results)} benchmark records.")


if __name__ == "__main__":
    main()
