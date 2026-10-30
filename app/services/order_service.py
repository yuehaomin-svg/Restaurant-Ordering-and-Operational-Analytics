from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Customer,
    DiningTable,
    MenuItem,
    OrderItem,
    OrderModel,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    Refund,
    PaymentStatus,
    TableStatus,
    local_now,
)
from app.schemas import CheckoutRequest, OrderCreate, OrderItemCreate, RefundRequest


def _order_number() -> str:
    return f"R-{uuid4().hex[:10].upper()}"


def _get_order_for_update(database: Session, order_id: int) -> OrderModel:
    order = database.scalar(
        select(OrderModel)
        .options(selectinload(OrderModel.items), selectinload(OrderModel.payments).selectinload(Payment.refunds))
        .where(OrderModel.id == order_id)
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def create_order(database: Session, payload: OrderCreate) -> OrderModel:
    dining_table = database.scalar(
        select(DiningTable).where(DiningTable.id == payload.table_id).with_for_update()
    )
    if dining_table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dining table not found")
    if dining_table.status != TableStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dining table is not available")

    customer = None
    if payload.customer_phone:
        customer = database.scalar(select(Customer).where(Customer.phone == payload.customer_phone))
        if customer is None:
            customer = Customer(phone=payload.customer_phone)
            database.add(customer)
            database.flush()

    order = OrderModel(order_no=_order_number(), table_id=dining_table.id, customer_id=customer.id if customer else None)
    dining_table.status = TableStatus.OCCUPIED
    database.add(order)
    database.flush()
    database.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.OPEN))
    database.commit()
    database.expire_all()
    return _get_order_for_update(database, order.id)


def add_order_item(database: Session, order_id: int, payload: OrderItemCreate) -> OrderModel:
    order = _get_order_for_update(database, order_id)
    if order.status != OrderStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only open orders can be changed")

    menu_item = database.scalar(select(MenuItem).where(MenuItem.id == payload.menu_item_id))
    if menu_item is None or not menu_item.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Available menu item not found")

    order_item = next((item for item in order.items if item.menu_item_id == menu_item.id), None)
    if order_item is None:
        database.add(OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=payload.quantity,
            unit_price=menu_item.price,
            line_total=menu_item.price * payload.quantity,
        ))
    else:
        order_item.quantity += payload.quantity
        order_item.line_total = order_item.unit_price * order_item.quantity

    database.commit()
    database.expire_all()
    return _get_order_for_update(database, order_id)


def checkout_order(database: Session, order_id: int, payload: CheckoutRequest) -> OrderModel:
    order = _get_order_for_update(database, order_id)
    if order.status != OrderStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only open orders can be checked out")
    if not order.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot checkout an empty order")

    total_amount = sum((item.line_total for item in order.items), Decimal("0.00"))
    order.total_amount = total_amount
    order.status = OrderStatus.PAID
    order.closed_at = local_now()
    order.table.status = TableStatus.AVAILABLE
    database.add(Payment(order_id=order.id, amount=total_amount, method=payload.payment_method))
    database.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PAID))
    database.commit()
    database.expire_all()
    return _get_order_for_update(database, order_id)


def refund_order(database: Session, order_id: int, payload: RefundRequest) -> OrderModel:
    order = _get_order_for_update(database, order_id)
    if order.status not in {OrderStatus.PAID, OrderStatus.PARTIALLY_REFUNDED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order cannot be refunded")
    if not order.payments:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order has no completed payment")

    payment = order.payments[-1]
    already_refunded = sum((refund.amount for refund in payment.refunds), Decimal("0.00"))
    remaining = payment.amount - already_refunded
    refund_amount = payload.amount or remaining
    if refund_amount <= 0 or refund_amount > remaining:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid refund amount")

    database.add(Refund(payment_id=payment.id, amount=refund_amount, reason=payload.reason))
    if already_refunded + refund_amount == payment.amount:
        payment.status = PaymentStatus.REFUNDED
        order.status = OrderStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED
        order.status = OrderStatus.PARTIALLY_REFUNDED
    database.add(OrderStatusHistory(order_id=order.id, status=order.status))
    database.commit()
    database.expire_all()
    return _get_order_for_update(database, order_id)
