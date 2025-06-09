from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.genres import (
    GenreCreateSchema,
    GenreUpdateSchema,
    GenreListItemSchema,
    GenreListResponseSchema,
    GenreDetailSchema,
    GenreFilterSchema,
    SortField,
    SortOrder
)
from schemas.movies import MovieListResponseSchema
from crud.genres import (
    get_genre_list_db,
    get_genre_by_id_db,
    create_genre_db,
    update_genre_db,
    delete_genre_db,
    get_movies_by_genre_db
)

router = APIRouter()


@router.get(
    "/genres/",
    response_model=GenreListResponseSchema,
    summary="Get paginated list of genres with movie counts",
    description=(
        "<h3>This endpoint retrieves a paginated list of genres from the database, "
        "including the number of movies in each genre.</h3>"
        "<p>The response includes details about the genres, total pages, and total items, "
        "along with links to the previous and next pages if applicable.</p>"
        "<h4>Sorting options:</h4>"
        "<ul>"
        "<li>sort_by: Field to sort by (name, movie_count)</li>"
        "<li>sort_order: Sort order (asc/desc)</li>"
        "</ul>"
    )
)
async def get_genre_list(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort_by: SortField = Query(None, description="Field to sort by"),
    sort_order: SortOrder = Query(None, description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch a paginated list of genres with movie counts from the database.

    :param request: The FastAPI request object
    :param page: The page number to retrieve (1-based index)
    :param per_page: The number of items per page
    :param sort_by: Field to sort by (name or movie_count)
    :param sort_order: Sort order (asc or desc)
    :param db: Asynchronous SQLAlchemy session
    :return: Paginated list of genres with movie counts
    """
    filters = GenreFilterSchema(sort_by=sort_by, sort_order=sort_order)
    genres_with_counts, total_items = await get_genre_list_db(db, page, per_page, filters)
    
    # Convert to response format
    genres = [
        GenreListItemSchema(
            id=genre.id,
            name=genre.name,
            movie_count=movie_count
        )
        for genre, movie_count in genres_with_counts
    ]

    return GenreListResponseSchema(
        genres=genres,
        total=total_items,
        prev_page=f"/genres/?page={page-1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/genres/?page={page+1}&per_page={per_page}" if total_items > page * per_page else None,
    )


@router.get(
    "/genres/{genre_id}/",
    response_model=GenreDetailSchema,
    summary="Get genre by ID with movie count"
)
async def get_genre_by_id(genre_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific genre by its ID, including the count of movies in that genre.

    :param genre_id: Unique identifier of the genre
    :param db: Asynchronous SQLAlchemy session
    :return: Genre details with movie count
    """
    genre = await get_genre_by_id_db(db, genre_id)
    return GenreDetailSchema.model_validate(genre)


@router.get(
    "/genres/{genre_id}/movies/",
    response_model=MovieListResponseSchema,
    summary="Get movies for a specific genre"
)
async def get_genre_movies(
    genre_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a paginated list of movies for a specific genre.

    :param genre_id: Unique identifier of the genre
    :param request: The FastAPI request object
    :param page: The page number to retrieve (1-based index)
    :param per_page: The number of items per page
    :param db: Asynchronous SQLAlchemy session
    :return: Paginated list of movies in the genre
    """
    movies = await get_movies_by_genre_db(db, genre_id, page, per_page)
    
    # Calculate pagination metadata
    total_items = len(movies)
    base_url = str(request.base_url)
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page+1}&per_page={per_page}" if total_items > page * per_page else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=(total_items + per_page - 1) // per_page,
        total_items=total_items
    )


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

    :param genre_data: Data required to create a new genre
    :param db: Asynchronous SQLAlchemy session
    :return: The created genre data
    """
    genre = await create_genre_db(db, genre_data)
    return GenreDetailSchema.model_validate(genre)


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

    :param genre_id: Unique identifier of the genre to update
    :param genre_data: Fields to update in the genre
    :param db: Asynchronous SQLAlchemy session
    :return: The updated genre data
    """
    genre = await update_genre_db(db, genre_id, genre_data)
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

    :param genre_id: Unique identifier of the genre to delete
    :param db: Asynchronous SQLAlchemy session
    :return: Success message confirming deletion
    """
    return await delete_genre_db(db, genre_id)
