from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import OrderModel
from app.schemas import CheckoutRequest, OrderCreate, OrderItemCreate, OrderRead, RefundRequest
from app.services.order_service import add_order_item, checkout_order, create_order, refund_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(limit: int = Query(default=50, ge=1, le=200), database: Session = Depends(get_db)) -> list[OrderModel]:
    return list(database.scalars(
        select(OrderModel)
        .options(selectinload(OrderModel.items), selectinload(OrderModel.payments))
        .order_by(OrderModel.placed_at.desc())
        .limit(limit)
    ))


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, database: Session = Depends(get_db)) -> OrderModel:
    order = database.scalar(
        select(OrderModel)
        .options(selectinload(OrderModel.items), selectinload(OrderModel.payments))
        .where(OrderModel.id == order_id)
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def post_order(payload: OrderCreate, database: Session = Depends(get_db)) -> OrderModel:
    return create_order(database, payload)


@router.post("/{order_id}/items", response_model=OrderRead)
def post_order_item(order_id: int, payload: OrderItemCreate, database: Session = Depends(get_db)) -> OrderModel:
    return add_order_item(database, order_id, payload)


@router.post("/{order_id}/checkout", response_model=OrderRead)
def post_checkout(order_id: int, payload: CheckoutRequest, database: Session = Depends(get_db)) -> OrderModel:
    return checkout_order(database, order_id, payload)


@router.post("/{order_id}/refund", response_model=OrderRead)
def post_refund(order_id: int, payload: RefundRequest, database: Session = Depends(get_db)) -> OrderModel:
    return refund_order(database, order_id, payload)
