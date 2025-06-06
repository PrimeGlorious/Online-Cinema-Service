from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import get_db, GenreModel
from schemas.genres import (
    GenreCreateSchema,
    GenreResponseSchema,
    GenreListResponseSchema
)

genre_router = APIRouter()


@genre_router.get(
    "/genres/",
    response_model=GenreListResponseSchema,
    summary="Get a list of all genres",
    description="<h3>Returns a list of all genres in the database.</h3>",
    responses={
        200: {"description": "Genres retrieved successfully."},
        404: {
            "description": "No genres found.",
            "content": {"application/json": {"example": {"detail": "No genres found."}}}
        }
    }
)
async def get_genres(
    db: AsyncSession = Depends(get_db),
) -> GenreListResponseSchema:
    """
    Retrieve all genres from the database.

    This endpoint returns a list of all genres stored in the database.

    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A list of all genres.
    :rtype: GenreListResponseSchema

    :raises HTTPException:
        - 404 if no genres are found in the database.
    """
    result = await db.execute(select(GenreModel))
    genres = result.scalars().all()

    if not genres:
        raise HTTPException(status_code=404, detail="No genres found.")

    return GenreListResponseSchema(genres=genres)


@genre_router.post(
    "/genres/",
    response_model=GenreResponseSchema,
    summary="Create a new genre",
    description="<h3>Add a new genre to the database.</h3>",
    status_code=201,
    responses={
        201: {"description": "Genre created successfully."},
        400: {"description": "Invalid input."},
        409: {"description": "Genre already exists."},
    },
)
async def create_genre(
    genre_data: GenreCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> GenreResponseSchema:
    """
    Create a new genre in the database.

    This endpoint allows the creation of a new genre with a unique name.

    :param genre_data: The data required to create a new genre.
    :type genre_data: GenreCreateSchema
    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The created genre with its details.
    :rtype: GenreResponseSchema

    :raises HTTPException:
        - 409 if a genre with the same name already exists.
        - 400 if the input data is invalid.
    """
    existing = await db.execute(select(GenreModel).where(GenreModel.name == genre_data.name))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Genre already exists.")

    try:
        genre = GenreModel(name=genre_data.name)
        db.add(genre)
        await db.commit()
        await db.refresh(genre)
        return GenreResponseSchema.model_validate(genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@genre_router.delete(
    "/genres/{genre_id}/",
    summary="Delete a genre by ID",
    description="<h3>Delete a genre from the database using its ID.</h3>",
    status_code=204,
    responses={
        204: {"description": "Genre deleted successfully."},
        404: {
            "description": "Genre not found.",
            "content": {"application/json": {"example": {"detail": "Genre not found."}}}
        }
    }
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a genre by its ID.

    This endpoint removes a genre from the database based on the provided ID.

    :param genre_id: The ID of the genre to be deleted.
    :type genre_id: int
    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException:
        - 404 if the genre with the given ID is not found.
    """
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")

    await db.delete(genre)
    await db.commit()


@genre_router.get(
    "/genres/{genre_id}/",
    response_model=GenreResponseSchema,
    summary="Get a genre by ID",
    description="<h3>Fetch a genre's details by its ID.</h3>",
    responses={
        404: {
            "description": "Genre not found.",
            "content": {"application/json": {"example": {"detail": "Genre not found."}}}
        }
    }
)
async def get_genre_by_id(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
) -> GenreResponseSchema:
    """
    Retrieve details of a genre by its ID.

    This endpoint returns detailed information about a specific genre.

    :param genre_id: The ID of the genre to retrieve.
    :type genre_id: int
    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The genre with the given ID.
    :rtype: GenreResponseSchema

    :raises HTTPException:
        - 404 if the genre is not found.
    """
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return GenreResponseSchema.model_validate(genre)
