from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, HttpUrl

from database.models.payments import PaymentStatusEnum


class PaymentCreateSchema(BaseModel):
    order_id: int


class StripePaymentResponseSchema(BaseModel):
    payment_id: int
    checkout_url: HttpUrl
    status: PaymentStatusEnum


class PaymentReadSchema(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    status: PaymentStatusEnum
    created_at: datetime
    external_payment_id: Optional[str] = None

    model_config = {"from_attributes": True}
