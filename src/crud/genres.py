from sqlalchemy import select, func, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from database.models.movies import GenreModel, MovieModel
from schemas.genres import (
    GenreCreateSchema,
    GenreUpdateSchema,
    GenreDetailSchema,
    GenreFilterSchema,
    SortField,
    SortOrder
)


async def get_genre_list_db(
    db: AsyncSession,
    page: int,
    per_page: int,
    filters: GenreFilterSchema
):
    offset = (page - 1) * per_page

    # Base query to get genres with movie counts
    base_query = (
        select(
            GenreModel,
            func.count(MovieModel.id).label('movie_count')
        )
        .outerjoin(MovieModel.genres)
        .group_by(GenreModel.id)
    )

    # Apply sorting
    if filters.sort_by == SortField.NAME:
        if filters.sort_order == SortOrder.DESC:
            base_query = base_query.order_by(desc(GenreModel.name))
        else:
            base_query = base_query.order_by(asc(GenreModel.name))
    elif filters.sort_by == SortField.MOVIE_COUNT:
        if filters.sort_order == SortOrder.DESC:
            base_query = base_query.order_by(desc('movie_count'))
        else:
            base_query = base_query.order_by(asc('movie_count'))
    else:
        # Default sorting by name ascending
        base_query = base_query.order_by(asc(GenreModel.name))

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_items = (await db.execute(count_query)).scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No genres found.")

    # Apply pagination
    base_query = base_query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(base_query)
    genres_with_counts = result.all()

    return genres_with_counts, total_items


async def get_genre_by_id_db(db: AsyncSession, genre_id: int):
    # Get genre with movie count
    stmt = (
        select(
            GenreModel,
            func.count(MovieModel.id).label('movie_count')
        )
        .outerjoin(MovieModel.genres)
        .where(GenreModel.id == genre_id)
        .group_by(GenreModel.id)
    )
    
    result = await db.execute(stmt)
    genre_with_count = result.first()
    
    if not genre_with_count:
        raise HTTPException(status_code=404, detail="Genre not found.")
    
    genre, movie_count = genre_with_count
    genre.movie_count = movie_count
    return genre


async def get_movies_by_genre_db(
    db: AsyncSession,
    genre_id: int,
    page: int,
    per_page: int
):
    offset = (page - 1) * per_page

    # Query to get movies for the specified genre
    stmt = (
        select(MovieModel)
        .join(MovieModel.genres)
        .where(GenreModel.id == genre_id)
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail=f"No movies found for genre ID {genre_id}")

    return movies


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
