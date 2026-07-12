from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from database.models.movies import StarModel
from schemas.stars import StarCreateSchema, StarUpdateSchema


async def get_stars(db: AsyncSession, page: int, per_page: int):
    offset = (page - 1) * per_page

    count_stmt = select(func.count(StarModel.id))
    total_items = (await db.execute(count_stmt)).scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No stars found.")

    stmt = select(StarModel).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    stars = result.scalars().all()

    if not stars:
        raise HTTPException(status_code=404, detail="No stars found.")

    return stars, total_items


async def get_star_by_id(db: AsyncSession, star_id: int):
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    return star


async def create_star(db: AsyncSession, star_in: StarCreateSchema):
    new_star = StarModel(name=star_in.name)
    db.add(new_star)
    try:
        await db.commit()
        await db.refresh(new_star)
        return new_star
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Star with this name already exists.")


async def update_star(db: AsyncSession, star_id: int, star_in: StarUpdateSchema):
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    star.name = star_in.name
    try:
        await db.commit()
        await db.refresh(star)
        return star
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Star with this name already exists.")


async def delete_star(db: AsyncSession, star_id: int):
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    await db.delete(star)
    await db.commit()
