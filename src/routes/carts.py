from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from loguru import logger

from crud.carts import create_cart_logic, add_cart_item_logic, remove_cart_item_logic, clear_cart_logic, \
    retrieve_cart_content_list_logic
from database import (
    get_db,
    MovieModel,
)

from schemas.carts import (
    CartCreationRequestSchema,
    CartCreationResponseSchema,
    CartItemAddResponseSchema,
    CartItemAddRequestSchema,
    CartItemRemoveRequestSchema,
    MessageResponseSchema,
    CartClearRequestSchema,
    CartItemListResponseSchema,
    CartItemListRequestSchema
)
from security.interfaces import JWTAuthManagerInterface

from database.models.carts import CartModel, CartItemModel


router = APIRouter()

@router.post(
    "/carts/create/",
    response_model=CartCreationResponseSchema,
    summary="Shopping cart creation",
    description="<h3>The endpoint for creating a shopping "
                "cart for a registered user.<h3/>",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Conflict - a shopping cart for the user already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Conflict - a shopping cart for the user already exists."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during shopping cart creation.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during shopping cart creation"
                    }
                }
            },
        },
    }
)
async def create_cart(
    cart_data: CartCreationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> CartCreationResponseSchema:
    return await create_cart_logic(cart_data, db)


@router.post(
    "/carts/add/",
    response_model=CartItemAddResponseSchema,
    summary="Adding cart item to the shopping cart",
    description="<h3> The endpoint for adding cart item (movie) to the shopping "
                "cart by cart ID and cart item ID.",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "The shopping cart and / or the movie with passed"
                           "ids not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The shopping cart and / or "
                                  "the movie doesn't exist."
                    }
                }
            },
        },
        409: {
            "description": "Conflict - the item is already in the shopping cart.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Conflict - the item is already in the shopping cart."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during adding the item to the shopping cart.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during adding the item to the shopping cart."
                    }
                }
            },
        },
    }
)
async def add_cart_item(
    cart_item_data: CartItemAddRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> CartItemAddResponseSchema:
    return await add_cart_item_logic(cart_item_data, db)


@router.post(
    "/carts/remove/",
    response_model=MessageResponseSchema,
    summary="Removing cart item from the shopping cart",
    description="<h3>The endpoint for removing cart item from the shopping cart "
                "by cart item ID and cart ID.</h3>",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "The shopping cart is empty.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The shopping cart is empty."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during removing "
                           "the item from the shopping cart.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during removing the item from the shopping cart."
                    }
                }
            },
        },
    }
)
async def remove_cart_item(
    cart_item_data: CartItemAddRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> CartItemAddResponseSchema:
    return await remove_cart_item_logic(cart_item_data, db)


@router.post(
    "/carts/clear/",
    response_model=MessageResponseSchema,
    summary="Removing all cart items from the shopping cart",
    description="<h3>The endpoint for removing all cart items from the shopping "
                "cart by ID.</h3>",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "There is no items in the shopping cart.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "There is no items in the shopping cart."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during removing items from the shopping cart.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during removing items from the shopping cart."
                    }
                }
            },
        },
    }
)
async def clear_cart_item(
    cart_data: CartClearRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> CartItemAddResponseSchema:
    return await clear_cart_logic(cart_data, db)


@router.post(
    "/carts/cart_item_list/",
    response_model=list[CartItemListResponseSchema],
    summary="Retrieving a list of items in the cart",
    description=(
        "This endpoint retrieves a list of items in one cart (for one user) from the database. "
        "For each movie in the cart, the title, price, genre, and release year are displayed."
    ),
    responses={
        404: {
            "description": "No movies in the cart found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found in the cart."}
                }
            },
        }
    }
)
async def retrieve_cart_content_list(
    cart_data: CartClearRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> CartItemAddResponseSchema:
    return await retrieve_cart_content_list_logic(cart_data, db)
