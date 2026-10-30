from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus, PaymentMethod, PaymentStatus, TableStatus


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class CategoryRead(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MenuItemCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    price: Decimal = Field(ge=0, decimal_places=2)
    is_available: bool = True


class MenuItemRead(MenuItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DiningTableCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    capacity: int = Field(gt=0, le=100)
    status: TableStatus = TableStatus.AVAILABLE


class DiningTableRead(DiningTableCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderCreate(BaseModel):
    table_id: int
    customer_phone: str | None = Field(default=None, max_length=30)


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0, le=100)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CheckoutRequest(BaseModel):
    payment_method: PaymentMethod


class RefundRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    reason: str | None = Field(default=None, max_length=255)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    paid_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_no: str
    table_id: int
    customer_id: int | None
    status: OrderStatus
    total_amount: Decimal
    placed_at: datetime
    closed_at: datetime | None
    items: list[OrderItemRead]
    payments: list[PaymentRead]
