import argparse
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import (
    Customer,
    DiningTable,
    MenuCategory,
    MenuItem,
    OrderItem,
    OrderModel,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Refund,
    TableStatus,
)


CATEGORY_DATA = {
    "Starters": [("Spring Rolls", 38), ("Tomato Soup", 42), ("Chicken Wings", 55)],
    "Main Courses": [("Grilled Chicken", 88), ("Beef Burger", 82), ("Seafood Pasta", 95), ("Vegetable Curry", 72)],
    "Drinks": [("Iced Lemon Tea", 26), ("Sparkling Water", 22), ("Coffee", 32)],
}


def ensure_reference_data(database: Session, randomizer: random.Random) -> tuple[list[MenuItem], list[DiningTable], list[Customer]]:
    if database.scalar(select(MenuCategory)) is None:
        for category_name, item_data in CATEGORY_DATA.items():
            category = MenuCategory(name=category_name)
            database.add(category)
            database.flush()
            for item_name, price in item_data:
                database.add(MenuItem(category_id=category.id, name=item_name, price=Decimal(price)))

    if database.scalar(select(DiningTable)) is None:
        for table_number in range(1, 13):
            database.add(DiningTable(name=f"T-{table_number:02d}", capacity=randomizer.choice([2, 4, 4, 6]), status=TableStatus.AVAILABLE))

    if database.scalar(select(Customer)) is None:
        for customer_number in range(1, 181):
            database.add(Customer(phone=f"138{customer_number:08d}", name=f"Customer {customer_number}"))
    database.flush()
    return (
        list(database.scalars(select(MenuItem))),
        list(database.scalars(select(DiningTable))),
        list(database.scalars(select(Customer))),
    )


def seed_orders(database: Session, order_count: int, randomizer: random.Random) -> None:
    menu_items, tables, customers = ensure_reference_data(database, randomizer)
    customer_weights = [
        12 if index < 15 else 5 if index < 55 else 2 if index < 110 else 1
        for index in range(len(customers))
    ]
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)

    for sequence in range(order_count):
        placed_at = base_time + timedelta(
            days=randomizer.randrange(30),
            hours=randomizer.choices([11, 12, 13, 18, 19, 20, 21], weights=[2, 5, 4, 5, 8, 7, 3])[0],
            minutes=randomizer.randrange(60),
        )
        chosen_items = randomizer.sample(menu_items, k=randomizer.randint(1, min(5, len(menu_items))))
        total_amount = Decimal("0.00")
        order = OrderModel(
            order_no=f"R-SEED-{sequence + 1:07d}",
            table_id=randomizer.choice(tables).id,
            customer_id=randomizer.choices(customers, weights=customer_weights, k=1)[0].id if randomizer.random() < 0.62 else None,
            status=OrderStatus.PAID,
            placed_at=placed_at,
            closed_at=placed_at + timedelta(minutes=randomizer.randint(25, 95)),
        )
        database.add(order)
        database.flush()

        for item in chosen_items:
            quantity = randomizer.randint(1, 3)
            line_total = item.price * quantity
            total_amount += line_total
            database.add(OrderItem(
                order_id=order.id,
                menu_item_id=item.id,
                quantity=quantity,
                unit_price=item.price,
                line_total=line_total,
            ))

        order.total_amount = total_amount
        payment = Payment(
            order_id=order.id,
            amount=total_amount,
            method=randomizer.choice(list(PaymentMethod)),
            status=PaymentStatus.COMPLETED,
            paid_at=order.closed_at,
        )
        database.add(payment)
        database.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PAID, changed_at=order.closed_at))

        refund_chance = randomizer.random()
        if refund_chance < 0.035:
            refund_amount = total_amount
            payment.status = PaymentStatus.REFUNDED
            order.status = OrderStatus.REFUNDED
            database.add(Refund(payment=payment, amount=refund_amount, reason="Service issue", refunded_at=order.closed_at + timedelta(hours=1)))
        elif refund_chance < 0.07:
            refund_amount = Decimal(randomizer.randint(10, 40)).quantize(Decimal("0.01"))
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
            order.status = OrderStatus.PARTIALLY_REFUNDED
            database.add(Refund(payment=payment, amount=refund_amount, reason="Item adjustment", refunded_at=order.closed_at + timedelta(hours=1)))

        if sequence and sequence % 500 == 0:
            database.commit()
            database.expunge_all()
        if sequence and sequence % 10_000 == 0:
            print(f"Generated {sequence} orders.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create reference data and reproducible restaurant transactions.")
    parser.add_argument("--orders", type=int, default=1000, help="Number of historical paid orders to generate.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding.")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    randomizer = random.Random(5003)
    database = SessionLocal()
    try:
        seed_orders(database, args.orders, randomizer)
        database.commit()
        print(f"Seeded {args.orders} orders.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
