# utils.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.accounts import UserGroupModel, UserGroupEnum

async def seed_user_groups(db: AsyncSession) -> None:
    """
    Перевіряє наявні групи в БД і додає ті, яких бракує.
    """
    result = await db.scalars(select(UserGroupModel.name))
    existing: set[UserGroupEnum] = set(result.all())

    for group in UserGroupEnum:
        if group not in existing:
            db.add(UserGroupModel(name=group))

    await db.flush()
