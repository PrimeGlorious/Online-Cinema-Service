from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models.movies import GenreModel
from schemas.genres import (
    GenreCreateSchema,
    GenreUpdateSchema,
    GenreListItemSchema,
    GenreListResponseSchema,
    GenreDetailSchema
)

router = APIRouter()


@router.get(
    "/genres/",
    response_model=GenreListResponseSchema,
    summary="Get paginated list of genres"
)
async def get_genre_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch a paginated list of genres from the database (asynchronously).

    Retrieves a list of genres based on the provided page number and number of items per page.
    Returns metadata including total item count and navigation links to previous/next pages.

    :param page: The page number to retrieve (1-based index, must be >= 1).
    :type page: int
    :param per_page: The number of items per page (between 1 and 50).
    :type per_page: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Paginated list of genres with total count and navigation links.
    :rtype: GenreListResponseSchema

    :raises HTTPException: 404 error if no genres are found.
    """
    offset = (page - 1) * per_page

    total_items = (await db.execute(select(func.count(GenreModel.id)))).scalar()
    if not total_items:
        raise HTTPException(status_code=404, detail="No genres found.")

    genres = (
        await db.execute(
            select(GenreModel)
            .offset(offset)
            .limit(per_page)
        )
    ).scalars().all()

    if not genres:
        raise HTTPException(status_code=404, detail="No genres found.")

    return GenreListResponseSchema(
        genres=[GenreListItemSchema.model_validate(g) for g in genres],
        total=total_items,
        prev_page=f"/genres/?page={page-1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/genres/?page={page+1}&per_page={per_page}" if total_items > page * per_page else None,
    )


@router.get(
    "/genres/{genre_id}/",
    response_model=GenreDetailSchema,
    summary="Get genre by ID"
)
async def get_genre_by_id(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific genre by its unique ID.

    Fetches the genre from the database using its primary key.

    :param genre_id: Unique identifier of the genre to retrieve.
    :type genre_id: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Genre detail data.
    :rtype: GenreDetailSchema

    :raises HTTPException: 404 error if the genre is not found.
    """
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return GenreDetailSchema.model_validate(genre)


@router.post(
    "/genres/",
    response_model=GenreDetailSchema,
    summary="Create new genre"
)
async def create_genre(
    genre_data: GenreCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new genre in the database.

    Accepts genre creation data and stores it as a new genre record.

    :param genre_data: Data required to create a new genre.
    :type genre_data: GenreCreateSchema
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: The created genre data.
    :rtype: GenreDetailSchema

    :raises HTTPException: 400 error if genre already exists.
    """
    new_genre = GenreModel(**genre_data.model_dump())
    db.add(new_genre)
    try:
        await db.commit()
        await db.refresh(new_genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Genre already exists.")
    return GenreDetailSchema.model_validate(new_genre)


@router.put(
    "/genres/{genre_id}/",
    response_model=GenreDetailSchema,
    summary="Update genre"
)
async def update_genre(
    genre_id: int,
    genre_data: GenreUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing genre by its ID.

    Applies the provided data to the genre with the specified ID.

    :param genre_id: Unique identifier of the genre to update.
    :type genre_id: int
    :param genre_data: Fields to update in the genre.
    :type genre_data: GenreUpdateSchema
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: The updated genre data.
    :rtype: GenreDetailSchema

    :raises HTTPException: 404 if genre not found, 400 on update conflict.
    """
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")

    for field, value in genre_data.model_dump(exclude_unset=True).items():
        setattr(genre, field, value)

    try:
        await db.commit()
        await db.refresh(genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Genre update conflict.")

    return GenreDetailSchema.model_validate(genre)


@router.delete(
    "/genres/{genre_id}/",
    summary="Delete genre by ID"
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a genre from the database by its ID.

    Removes the genre with the specified ID from the database.

    :param genre_id: Unique identifier of the genre to delete.
    :type genre_id: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Success message confirming deletion.
    :rtype: dict

    :raises HTTPException: 404 error if genre not found.
    """
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    await db.delete(genre)
    await db.commit()
    return {"detail": "Genre deleted successfully"}
