from datetime import datetime
from typing import Optional, List

from sqlalchemy import select

from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies.custom import get_current_user, require_admin
from database import get_db, UserModel, MovieModel
from database.models.carts import CartItemModel, CartModel
from database.models.orders import OrderItem, OrderModel, OrderStatusEnum
from schemas.orders import OrderCreateSchema, OrderReadSchema
from services.orders import get_user_movies_by_order_status

router = APIRouter()


@router.post(
    "/orders/",
    response_model=OrderReadSchema,
    summary="Order Creation",
    description="Create a new order.",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderReadSchema:
    stmt = await db.execute(
        select(CartModel).options(selectinload(CartModel.cart_items)).where(CartModel.user_id == current_user.id)
    )
    cart = stmt.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found for user.")

    if not cart.cart_items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Your shopping cart is empty."
        )

    cart_movie_ids = [item.movie_id for item in cart.cart_items]

    bought_movie_ids = await get_user_movies_by_order_status(
        db=db, user_id=current_user.id, status=OrderStatusEnum.PAID
    )

    for movie_id in data.movie_ids:
        if movie_id not in cart_movie_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Movie ID {movie_id} is not in your cart.",
            )

    movie_ids_to_order = [
        movie_id for movie_id in data.movie_ids if movie_id not in bought_movie_ids
    ]

    if not movie_ids_to_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All selected movies were already purchased.",
        )

    pending_movie_ids = await get_user_movies_by_order_status(
        db=db, user_id=current_user.id, status=OrderStatusEnum.PENDING
    )

    s_movie_ids_to_order, s_pending_movie_ids = set(movie_ids_to_order), set(
        pending_movie_ids
    )
    conflict_ids = s_movie_ids_to_order.intersection(s_pending_movie_ids)

    if conflict_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Some movies already have pending orders: {list(conflict_ids)}",
        )

    stmt_price = await db.execute(
        select(MovieModel.id, MovieModel.price).where(MovieModel.id.in_(movie_ids_to_order))
    )
    movie_price_map = {movie_id: price for movie_id, price in stmt_price.all()}
    total_amount = sum(movie_price_map.values())

    try:
        order = OrderModel(
            user_id=current_user.id,
            status=OrderStatusEnum.PENDING,
            created_at=datetime.utcnow(),
            total_amount=total_amount,
        )
        db.add(order)
        await db.flush()

        order_items = [
            OrderItem(
                order_id=order.id,
                movie_id=movie_id,
                price_at_order=movie_price_map[movie_id],
            )
            for movie_id in movie_ids_to_order
        ]
        db.add_all(order_items)
        await db.flush()
        await db.commit()

        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_items))
            .where(OrderModel.id == order.id)
        )
        result = await db.execute(stmt)
        order = result.scalar_one()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

    return OrderReadSchema.model_validate(order)


@router.get(
    "/admin/orders/",
    response_model=List[OrderReadSchema],
    summary="Admin: List all orders with filters",
)
async def list_all_orders(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(require_admin),
        status: Optional[OrderStatusEnum] = Query(None),
        user_id: Optional[int] = Query(None),
        from_date: Optional[datetime] = Query(None),
        to_date: Optional[datetime] = Query(None),
) -> List[OrderReadSchema]:
    stmt = select(OrderModel).options(selectinload(OrderModel.order_items))

    if status:
        stmt = stmt.where(OrderModel.status == status)
    if user_id:
        stmt = stmt.where(OrderModel.user_id == user_id)
    if from_date:
        stmt = stmt.where(OrderModel.created_at >= from_date)
    if to_date:
        stmt = stmt.where(OrderModel.created_at <= to_date)

    result = await db.execute(stmt)
    orders = result.scalars().all()
    return [OrderReadSchema.model_validate(order) for order in orders]


@router.get(
    "/orders/", response_model=List[OrderReadSchema], summary="List user's own orders"
)
async def list_my_orders(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
        status: Optional[OrderStatusEnum] = None,
) -> List[OrderReadSchema]:
    stmt = (
        select(OrderModel)
        .options(selectinload(OrderModel.order_items))
        .where(OrderModel.user_id == current_user.id)
    )

    if status:
        stmt = stmt.where(OrderModel.status == status)

    result = await db.execute(stmt)
    orders = result.scalars().all()
    return [OrderReadSchema.model_validate(order) for order in orders]


@router.get(
    "/orders/{order_id}",
    response_model=OrderReadSchema,
    summary="Get one of user's own orders",
)
async def get_my_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
) -> OrderReadSchema:
    stmt = (
        select(OrderModel)
        .options(selectinload(OrderModel.order_items))
        .where(OrderModel.id == order_id)
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only view your own orders."
        )

    return OrderReadSchema.model_validate(order)
