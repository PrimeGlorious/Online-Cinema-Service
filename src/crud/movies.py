from fastapi import HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel

from schemas.movies import MovieListResponseSchema, MovieListItemSchema


async def movie_list(
        request: Request,
        page: int,
        per_page: int,
        db: AsyncSession
) -> MovieListResponseSchema:
    """
        Fetch a paginated list of movies from the database (asynchronously).

        This function retrieves a paginated list of movies, allowing the client to specify
        the page number and the number of items per page. It calculates the total pages
        and provides links to the previous and next pages when applicable.

        :param page: The page number to retrieve (1-based index, must be >= 1).
        :type page: int
        :param per_page: The number of items to display per page (must be between 1 and 20).
        :type per_page: int
        :param db: The async SQLAlchemy database session (provided via dependency injection).
        :type db: AsyncSession

        :return: A response containing the paginated list of movies and metadata.
        :rtype: MovieListResponseSchema

        :raises HTTPException: Raises a 404 error if no movies are found for the requested page.
        """
    offset = (page - 1) * per_page

    count_stmt = select(func.count(MovieModel.id))
    result_count = await db.execute(count_stmt)
    total_items = result_count.scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    order_by = MovieModel.default_order_by()
    stmt = select(MovieModel)
    if order_by:
        stmt = stmt.order_by(*order_by)

    stmt = stmt.offset(offset).limit(per_page)

    result_movies = await db.execute(stmt)
    movies = result_movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_items + per_page - 1) // per_page

    url = request.url.path

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"{url}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"{url}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response
