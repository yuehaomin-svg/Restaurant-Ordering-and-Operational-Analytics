import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.models import DiningTable, OrderModel, TableStatus
from app.schemas import OrderCreate
from app.services.order_service import create_order


def create_test_table(database) -> DiningTable:
    dining_table = DiningTable(name=f"CONCURRENCY-{uuid4().hex[:8].upper()}", capacity=4, status=TableStatus.AVAILABLE)
    database.add(dining_table)
    database.commit()
    database.refresh(dining_table)
    return dining_table


def attempt_order(table_id: int, barrier: threading.Barrier) -> dict:
    barrier.wait()
    database = SessionLocal()
    try:
        order = create_order(database, OrderCreate(table_id=table_id))
        return {"status": "created", "order_id": order.id}
    except HTTPException as error:
        return {"status": "conflict", "status_code": error.status_code, "detail": error.detail}
    finally:
        database.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    database = SessionLocal()
    try:
        dining_table = create_test_table(database)
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(attempt_order, dining_table.id, barrier) for _ in range(2)]
            outcomes = [future.result() for future in futures]

        created = [outcome for outcome in outcomes if outcome["status"] == "created"]
        conflicts = [outcome for outcome in outcomes if outcome["status"] == "conflict"]
        result = {
            "created_orders": len(created),
            "conflicting_requests": len(conflicts),
            "outcomes": outcomes,
            "passed": len(created) == 1 and len(conflicts) == 1 and conflicts[0]["status_code"] == 409,
        }

        for outcome in created:
            order_id = outcome["order_id"]
            database.execute(text("DELETE FROM refunds WHERE payment_id IN (SELECT id FROM payments WHERE order_id = :order_id)"), {"order_id": order_id})
            database.execute(text("DELETE FROM payments WHERE order_id = :order_id"), {"order_id": order_id})
            database.execute(text("DELETE FROM order_status_history WHERE order_id = :order_id"), {"order_id": order_id})
            database.execute(text("DELETE FROM order_items WHERE order_id = :order_id"), {"order_id": order_id})
            database.execute(text("DELETE FROM orders WHERE id = :order_id"), {"order_id": order_id})
        database.delete(dining_table)
        database.commit()

        output_path = Path(__file__).resolve().parent.parent / "docs" / "concurrency_result.json"
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        if not result["passed"]:
            raise SystemExit(1)
    finally:
        database.close()


if __name__ == "__main__":
    main()
