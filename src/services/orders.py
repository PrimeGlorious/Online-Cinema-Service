from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.orders import OrderItem, OrderModel, OrderStatusEnum


async def get_user_movies_by_order_status(
    db: AsyncSession,
    user_id: int,
    status: OrderStatusEnum
) -> list[int]:
    stmt = (
        select(OrderItem.movie_id)
        .join(OrderModel, OrderItem.order_id == OrderModel.id)
        .where(OrderModel.user_id == user_id, OrderModel.status == status)
    )
    result = await db.execute(stmt)
    return list(result.scalars())
