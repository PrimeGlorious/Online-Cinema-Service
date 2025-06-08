from datetime import date

from pydantic import BaseModel


class CartCreationRequestSchema(BaseModel):
    user_id: int

    model_config = {
        "from_attributes": True
    }


class CartCreationResponseSchema(BaseModel):
    id: int

    model_config = {
        "from_attributes": True
    }


class CartItemAddRequestSchema(BaseModel):
    cart_id: int
    cart_item_id: int

    model_config = {
        "from_attributes": True
    }


class CartItemAddResponseSchema(BaseModel):
    id: int

    model_config = {
        "from_attributes": True
    }


class CartItemRemoveRequestSchema(BaseModel):

    cart_id: int
    cart_item_id: int

    model_config = {
        "from_attributes": True
    }


class CartItemRemoveResponseSchema(BaseModel):
    id: int

    model_config = {
        "from_attributes": True
    }


class MessageResponseSchema(BaseModel):
    message: str


class CartClearRequestSchema(BaseModel):
    cart_id: int

    model_config = {
        "from_attributes": True
    }


class CartItemListRequestSchema(BaseModel):
    cart_id: int


class CartItemListResponseSchema(BaseModel):
    cart_id: int
    movie_name: str
    movie_price: float
    movie_genres: list[str]
    movie_year: int

    model_config = {
        "from_attributes": True
    }
