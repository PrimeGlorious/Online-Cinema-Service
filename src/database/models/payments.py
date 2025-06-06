import enum
from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PaymentStatusEnum(str, enum.Enum):
    CANCELED = "canceled"
    SUCCESSFUL = "successful"
    PENDING = "pending"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum),
        default=PaymentStatusEnum.PENDING,
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    user = relationship("UserModel", back_populates="payments")
    order = relationship("OrderModel", back_populates="payments")

