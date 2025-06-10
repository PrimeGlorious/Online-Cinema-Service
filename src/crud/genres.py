from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from database.models.movies import GenreModel
from schemas.genres import GenreCreateSchema, GenreUpdateSchema, GenreDetailSchema


async def get_genre_list_db(db: AsyncSession, page: int, per_page: int):
    offset = (page - 1) * per_page

    total_items = (await db.execute(select(func.count(GenreModel.id)))).scalar()
    if not total_items:
        raise HTTPException(status_code=404, detail="No genres found.")

    genres = (
        await db.execute(
            select(GenreModel).offset(offset).limit(per_page)
        )
    ).scalars().all()

    if not genres:
        raise HTTPException(status_code=404, detail="No genres found.")

    return genres, total_items


async def get_genre_by_id_db(db: AsyncSession, genre_id: int):
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return genre


async def create_genre_db(db: AsyncSession, genre_data: GenreCreateSchema):
    new_genre = GenreModel(**genre_data.model_dump())
    db.add(new_genre)
    try:
        await db.commit()
        await db.refresh(new_genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Genre already exists.")
    return new_genre


async def update_genre_db(db: AsyncSession, genre_id: int, genre_data: GenreUpdateSchema):
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")

    update_data = genre_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(genre, field, value)

    try:
        await db.commit()
        await db.refresh(genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Genre update conflict.")

    return genre


async def delete_genre_db(db: AsyncSession, genre_id: int):
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    await db.delete(genre)
    await db.commit()
    return {"detail": "Genre deleted successfully"}
