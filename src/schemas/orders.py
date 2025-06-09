from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, field_validator

from database.models.orders import OrderStatusEnum


class OrderCreateSchema(BaseModel):
    movie_ids: List[int]

    @field_validator("movie_ids")
    @classmethod
    def validate_non_empty(cls, value: List[int]):
        if not value:
            raise ValueError("Movie list cannot be empty")
        return value


class OrderItemReadSchema(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal

    model_config = {
        "from_attributes": True
    }


class OrderReadSchema(BaseModel):
    id: int
    created_at: datetime
    order_items: List[OrderItemReadSchema]
    total_amount: Decimal
    status: OrderStatusEnum

    model_config = {
        "from_attributes": True
    }
