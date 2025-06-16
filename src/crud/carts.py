from typing import TypeVar, Type

from fastapi import Depends, status, HTTPException
from sqlalchemy import select, and_, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import (
    get_db,
    MovieModel,
    UserModel,
    CartModel, CartItemModel
)
from schemas.carts import (
    CartCreationResponseSchema,
    CartCreationRequestSchema,
    CartItemAddRequestSchema,
    CartItemAddResponseSchema,
    CartItemRemoveRequestSchema,
    MessageResponseSchema,
    CartClearRequestSchema,
    CartItemListRequestSchema,
    CartItemListResponseSchema
)


T = TypeVar("T")

async def get_instance_or_404(
    model: Type[T],
    db: AsyncSession,
    field: str,
    value,
    error_detail: str | None = None,
) -> T:
    """
    Get an instance of a model by field and value or raise HTTP 404.

    Args:
        model (Type[T]): The SQLAlchemy model class.
        db (AsyncSession): The database session.
        field (str): Name of the column to filter by (e.g., 'id').
        value (Any): The value to filter.
        error_detail (str): Optional error detail to show in 404.

    Returns:
        instance of the model if found, otherwise raises HTTPException(404)
    """
    column_attr = getattr(model, field)
    stmt = select(model).where(column_attr == value)
    result = await db.execute(stmt)
    instance = result.scalars().first()

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail or f"{model.__name__} with {field}={value} not found."
        )
    return instance





async def create_cart_logic(
    cart_data: CartCreationRequestSchema,
    db: AsyncSession = Depends(get_db),
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


async def add_cart_item_logic(
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
        cart_item_data (CartItemAddRequestSchema): The cart id and movie id are needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        CartItemAddResponseSchema: The newly added item details.

    Raises:
        HTTPException:
            - 400 If cart and / or cart item does not exist.
            - 409 Conflict if the item is already in the shopping cart.
            - 500 Internal Server Error if an error occurs during item adding.
    """
    _ = await get_instance_or_404(
        CartModel,
        db,
        field="id",
        value=cart_item_data.cart_id,
        error_detail=f"A shopping cart ID {cart_item_data.cart_id} does not exist."
    )

    current_cart_item_exists = select(MovieModel.id).where(MovieModel.id == cart_item_data.movie_id)
    result = await db.execute(current_cart_item_exists)
    current_cart_item_found = result.scalars().first()
    if not current_cart_item_found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Movie ID {cart_item_data.movie_id} does not exists."
        )

    current_cart_item = select(CartItemModel).where(
        and_(
            CartItemModel.movie_id == cart_item_data.movie_id,
            CartItemModel.cart_id == cart_item_data.cart_id
        )
    )

    result = await db.execute(current_cart_item)
    existing_cart_item = result.scalars().first()

    if existing_cart_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict - the item ID {cart_item_data.movie_id} was already added to "
                   f"the shopping card ID {cart_item_data.cart_id}."
        )

    try:
        new_cart_item = CartItemModel(
            cart_id=cart_item_data.cart_id,
            movie_id=cart_item_data.movie_id,
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


async def remove_cart_item_logic(
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
        cart_item_data (CartItemRemoveRequestSchema): The user id and movie id are needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageResponseSchema: The removed item details (message).

    Raises:
        HTTPException:
            - 400 There is no the item in the shopping cart.
            - 500 Internal Server Error if an error occurs during item removing.
    """
    _ = await get_instance_or_404(
        CartModel,
        db,
        field="id",
        value=cart_item_data.cart_id,
        error_detail=f"A shopping cart ID {cart_item_data.cart_id} does not exist."
    )

    exact_item = select(CartItemModel).where(
        and_(
            CartItemModel.movie_id == cart_item_data.movie_id,
            CartItemModel.cart_id == cart_item_data.cart_id

        )
    )
    result = await db.execute(exact_item)
    exact_cart_item = result.scalars().first()

    if not exact_cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item ID {cart_item_data.movie_id} not found in cart ID {cart_item_data.cart_id}."
        )

    try:
        if not exact_cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found. Surprise - it was checked.")
        await db.delete(exact_cart_item)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during deleting the movie from the shopping cart."
        ) from e
    else:
        message_str = f"Movie ID {cart_item_data.movie_id} has been successfully removed from the cart ID {cart_item_data.cart_id}."
        return MessageResponseSchema(message=message_str)


async def clear_cart_logic(
    cart_data: CartClearRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """
    Endpoint for removing all items from the shopping cart.

    Removes all items from the shopping cart (if any) from the shopping cart.
    If no items in the shopping cart, an HTTP 400 error is raised.
    In case of any unexpected issues during clearing process, an HTTP 500 error
    is returned.

    Args:
        cart_data (CartClearRequestSchema): The cart id solely is needed.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageResponseSchema: Text message for the user.

    Raises:
        HTTPException:
            - 400 There is no items in the shopping cart.
            - 500 Internal Server Error if an error occurs during item removing.
    """

    _ = await get_instance_or_404(
        CartModel,
        db,
        field="id",
        value=cart_data.cart_id,
        error_detail=f"A shopping cart ID {cart_data.cart_id} does not exist."
    )

    current_cart_items = select(CartItemModel).where(
        CartItemModel.cart_id == cart_data.cart_id
    )

    result = await db.execute(current_cart_items)
    existing_cart_items = result.scalars().all()
    if not existing_cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"There is no items in the shopping cart ID {cart_data.cart_id}."
        )

    try:
        await db.execute(
            delete(CartItemModel).where(CartItemModel.cart_id == cart_data.cart_id)
        )
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during deleting items from the shopping cart."
        ) from e
    else:
        message_str = f"The cart {cart_data.cart_id} has been successfully emptied."
        return MessageResponseSchema(message=message_str)


async def retrieve_cart_content_list_logic(
    cart_data: CartItemListRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> list[CartItemListResponseSchema]:

    cart_items = await db.execute(
        select(CartItemModel)
        .options(
            joinedload(CartItemModel.movie).joinedload(MovieModel.genres),
        )
        .where(CartItemModel.cart_id == cart_data.cart_id)
    )

    cart_items = cart_items.unique().scalars().all()

    if not cart_items:
        raise HTTPException(status_code=404, detail="No movies found in the cart.")

    return [
        CartItemListResponseSchema(
            cart_id=cart_item.cart_id,
            movie_name=cart_item.movie.name,
            movie_price=cart_item.movie.price,
            movie_genres=[genre.name for genre in cart_item.movie.genres],
            movie_year=cart_item.movie.year
        )
        for cart_item in cart_items
    ]
