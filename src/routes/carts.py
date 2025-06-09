from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from loguru import logger
from config import get_jwt_auth_manager, BaseAppSettings, get_accounts_email_notificator
from database import (
    get_db, MovieModel, UserModel,
)
from exceptions import BaseSecurityError
from notifications import EmailSenderInterface

from schemas.carts import (
    CartCreationRequestSchema,
    CartCreationResponseSchema,
    CartItemAddResponseSchema,
    CartItemAddRequestSchema,
    CartItemRemoveRequestSchema,
    CartItemRemoveResponseSchema,
    MessageResponseSchema,
    CartClearRequestSchema,
    CartItemListResponseSchema,
    CartItemListRequestSchema
)
from security.interfaces import JWTAuthManagerInterface

from database.models.carts import CartModel, CartItemModel

router = APIRouter()


@router.post(
    "/create/",
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
    # current_user: UserModel = Depends(get_current_user),
) -> CartCreationResponseSchema:
    """
    Endpoint for a shopping cart creation.

    Creates a shopping cart (if not exists already) for a current registered user.
    If the shopping cart for the user already exists, an HTTP 409 error is raised.
    In case of any unexpected issues during the creation process, an HTTP 500 error is returned.

    Args:
        cart_data (CartCreationRequestSchema): Only the user id is needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        CartCreationResponseSchema: The newly created shopping cart details.

    Raises:
        HTTPException:
            - 409 Conflict if a shopping cart for the user exists.
            - 500 Internal Server Error if an error occurs during shopping creation.
    """
    current_user = select(UserModel).where(UserModel.id == cart_data.user_id)
    result = await db.execute(current_user)
    existing_user = result.scalars().first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User ID {cart_data.user_id} doesn't exists."
        )

    current_cart = select(CartModel).where(CartModel.user_id == cart_data.user_id)
    result = await db.execute(current_cart)
    existing_cart = result.scalars().first()
    if existing_cart:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict - a shopping cart for the user ID {cart_data.user_id} already exists."
        )

    try:
        new_cart = CartModel(user_id=cart_data.user_id)
        db.add(new_cart)
        await db.commit()
        await db.refresh(new_cart)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during a shopping cart creation."
        ) from e
    else:
        return CartCreationResponseSchema.model_validate(new_cart)


@router.post(
    "/add/",
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
    """
    Endpoint for adding an item to the shopping cart.

    Adds an item to the shopping cart (if not there already) for the shopping cart.
    If the item is already in the shopping cart, an HTTP 409 error is raised.
    In case of any unexpected issues during the adding process, an HTTP 500 error
    is returned.

    Args:
        cart_item_data (CartItemAddRequestSchema): The user id and item id are needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        CartItemAddResponseSchema: The newly added item details.

    Raises:
        HTTPException:
            - 400 If cart and / or cart item does not exist.
            - 409 Conflict if the item is already in the shopping cart.
            - 500 Internal Server Error if an error occurs during item adding.
    """
    current_cart = select(CartModel).where(CartModel.id == cart_item_data.cart_id)
    result = await db.execute(current_cart)
    existing_cart = result.scalars().first()
    if not existing_cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A shopping cart {cart_item_data.cart_id} does not exists."
        )

    current_cart_item_exists = select(MovieModel.id).where(MovieModel.id == cart_item_data.cart_item_id)
    result = await db.execute(current_cart_item_exists)
    current_cart_item_found = result.scalars().first()
    if not current_cart_item_found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cart item ID {cart_item_data.cart_item_id} does not exists."
        )

    current_cart_item = select(CartItemModel).where(
        and_(
            CartItemModel.movie_id == cart_item_data.cart_item_id,
            CartItemModel.cart_id == cart_item_data.cart_id
        )
    )

    result = await db.execute(current_cart_item)
    existing_cart_item = result.scalars().first()

    if existing_cart_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict - the item ID {cart_item_data.cart_item_id} is already added to "
                   f"the shopping card ID {cart_item_data.cart_id}."
        )

    try:
        new_cart_item = CartItemModel(
            cart_id=cart_item_data.cart_id,
            movie_id=cart_item_data.cart_item_id,
        )
        db.add(new_cart_item)
        await db.commit()
        await db.refresh(new_cart_item)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during adding an item to the shopping cart."
        ) from e
    else:
        return CartItemAddResponseSchema.model_validate(new_cart_item)


@router.post(
    "/remove/",
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
    cart_item_data: CartItemRemoveRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema | None:
    """
    Endpoint for removing the item from the shopping cart.

    Removes the item from the shopping cart (if it is there) from the shopping cart.
    If the item is not in the shopping cart, an HTTP 400 error is raised.
    In case of any unexpected issues during the removing process, an HTTP 500 error
    is returned.

    Args:
        cart_item_data (CartItemRemoveRequestSchema): The user id and item id are needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageResponseSchema: The removed item details (message).

    Raises:
        HTTPException:
            - 400 There is no the item in the shopping cart.
            - 500 Internal Server Error if an error occurs during item removing.
    """
    current_cart = select(CartModel).where(CartModel.id == cart_item_data.cart_id)
    result = await db.execute(current_cart)
    existing_cart = result.scalars().first()
    if not existing_cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A shopping cart ID {cart_item_data.cart_id} does not exists."
        )

    logger.info("304 cart_item_id" + str(cart_item_data.cart_item_id))
    logger.info("305 cart_id" + str(cart_item_data.cart_id))
    # current_cart_item = select(CartItemModel).where(
    #     and_(
    #         CartItemModel.id == cart_item_data.cart_item_id,
    #         CartItemModel.cart_id == cart_item_data.cart_id
    #     )
    # )
    #
    # result = await db.execute(current_cart_item)
    # existing_cart_item = result.scalars().first()
    # if not existing_cart_item:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"There is no such an item in the shopping cart ID {cart_item_data.cart_id}."
    #     )

    stmt = select(CartItemModel).where(CartItemModel.id == cart_item_data.cart_item_id)
    result = await db.execute(stmt)
    cart_item = result.scalars().first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CartItem ID {cart_item_data.cart_item_id} not found."
        )

    if cart_item.cart_id != cart_item_data.cart_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item ID {cart_item_data.cart_item_id} not found in cart ID {cart_item_data.cart_id}."
        )

    try:
        logger.info("321 cart_item_id" + str(cart_item_data.cart_id))
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found. Surprise - it was checked.")
        await db.delete(cart_item)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during deleting an item from the shopping cart."
        ) from e
    else:
        message_str = f"Item {cart_item_data.cart_item_id} has been successfully removed from the cart ID {cart_item_data.cart_id}."
        return MessageResponseSchema(message=message_str)


@router.post(
    "/clear/",
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
async def clear_cart(
    cart_item_data: CartClearRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """
    Endpoint for removing all items from the shopping cart.

    Removes all items from the shopping cart (if any) from the shopping cart.
    If no items in the shopping cart, an HTTP 400 error is raised.
    In case of any unexpected issues during clearing process, an HTTP 500 error
    is returned.

    Args:
        cart_item_data (CartClearRequestSchema): The user id solely is needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageResponseSchema: Text message for the user.

    Raises:
        HTTPException:
            - 400 There is no items in the shopping cart.
            - 500 Internal Server Error if an error occurs during item removing.
    """
    logger.info("388 ", str(cart_item_data.cart_id))
    current_cart = select(CartModel).where(CartModel.id == cart_item_data.cart_id)
    result = await db.execute(current_cart)
    existing_cart = result.scalars().first()
    if not existing_cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A shopping cart ID {cart_item_data.cart_id} does not exists."
        )
    logger.info("396 ", str(cart_item_data.cart_id))
    current_cart_items = select(CartItemModel).where(
        CartItemModel.cart_id == cart_item_data.cart_id
    )
    logger.info("401")
    result = await db.execute(current_cart_items)
    existing_cart_items = result.scalars().all()
    logger.info("403  ", str(existing_cart_items))
    if not existing_cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"There is no items in the shopping cart ID {cart_item_data.cart_id}."
        )

    try:
        await db.execute(
            delete(CartItemModel).where(CartItemModel.cart_id == cart_item_data.cart_id)
        )
        await db.commit()

        logger.info("416")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during deleting items from the shopping cart."
        ) from e
    else:
        message_str = f"The cart {cart_item_data.cart_id} has been successfully emptied."
        return MessageResponseSchema(message=message_str)


@router.post(
    "/cart_item_list/",
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
    cart_data: CartItemListRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> list[CartItemListResponseSchema]:
    logger.info("cart_data 481 ")
    result = await db.execute(
        select(CartItemModel)
        .options(selectinload(CartItemModel.movie))
        .where(CartItemModel.cart_id == cart_data.cart_id)
    )
    logger.info("cart_data 487 ")

    cart_items = await db.execute(
        select(CartItemModel)
        .options(
            joinedload(CartItemModel.movie).joinedload(MovieModel.genres),
        )
        .where(CartItemModel.cart_id == cart_data.cart_id)
    )

    cart_items = await db.execute(
        select(CartItemModel)
        .options(
            joinedload(CartItemModel.movie).joinedload(MovieModel.genres),
        )
        .where(CartItemModel.cart_id == 3)
    )
    logger.info("cart_data 504 ")
    # print("cart_items 418 ", cart_items)
    cart_items = cart_items.scalars().all()
    # print("cart_items 420 ", cart_items)
    if not cart_items:
        raise HTTPException(status_code=404, detail="No movies found in the cart.")

    return [
        CartItemListResponseSchema(
            cart_id=cart_item.cart_id,
            movie_name=cart_item.movie.name,
            # movie_price=cart_item.movie.price,
            movie_genres=[genre.name for genre in cart_item.movie.genres],
            movie_date=cart_item.movie.date
        )
        for cart_item in cart_items
    ]
