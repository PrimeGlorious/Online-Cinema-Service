import enum
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        Enum(OrderStatusEnum),
        nullable=False,
        default=OrderStatusEnum.PENDING
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="order")

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    order_items: Mapped["OrderItem"] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False
    )
    price_at_order: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["OrderModel"] = relationship(
        "OrderModel",
        back_populates="order_items"
    )

    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="order_items"
    )
