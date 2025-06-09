from fastapi import HTTPException, Request
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel
from database.models.movies import (
    CertificationModel,
    GenreModel,
    StarModel,
    DirectorModel
)

from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieFilterSchema,
    SortField,
    SortOrder
)


async def movie_list(
        request: Request,
        page: int,
        per_page: int,
        db: AsyncSession,
        filters: MovieFilterSchema
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
        :param filters: Filter criteria for the movies.
        :type filters: MovieFilterSchema

        :return: A response containing the paginated list of movies and metadata.
        :rtype: MovieListResponseSchema

        :raises HTTPException: Raises a 404 error if no movies are found for the requested page.
        """
    offset = (page - 1) * per_page

    # Base query
    base_query = select(MovieModel)

    # Apply filters
    if filters.date_from is not None:
        base_query = base_query.where(MovieModel.date >= filters.date_from)
    if filters.date_to is not None:
        base_query = base_query.where(MovieModel.date <= filters.date_to)
    if filters.score_from is not None:
        base_query = base_query.where(MovieModel.score >= filters.score_from)
    if filters.score_to is not None:
        base_query = base_query.where(MovieModel.score <= filters.score_to)
    if filters.price_from is not None:
        base_query = base_query.where(MovieModel.price >= filters.price_from)
    if filters.price_to is not None:
        base_query = base_query.where(MovieModel.price <= filters.price_to)

    # Apply search
    if filters.search:
        search_term = f"%{filters.search}%"
        base_query = base_query.join(MovieModel.directors).join(MovieModel.stars).where(
            or_(
                MovieModel.name.ilike(search_term),
                MovieModel.overview.ilike(search_term),
                DirectorModel.name.ilike(search_term),
                StarModel.name.ilike(search_term)
            )
        )

    # Apply genre filter
    if filters.genre:
        base_query = base_query.join(MovieModel.genres).where(GenreModel.name == filters.genre)

    # Apply certification filter
    if filters.certification:
        base_query = base_query.join(MovieModel.certification).where(CertificationModel.name == filters.certification)

    # Apply director filter
    if filters.director:
        base_query = base_query.join(MovieModel.directors).where(DirectorModel.name == filters.director)

    # Apply star filter
    if filters.star:
        base_query = base_query.join(MovieModel.stars).where(StarModel.name == filters.star)

    # Apply sorting
    if filters.sort_by:
        sort_column = getattr(MovieModel, filters.sort_by.value)
        if filters.sort_order == SortOrder.DESC:
            base_query = base_query.order_by(desc(sort_column))
        else:
            base_query = base_query.order_by(asc(sort_column))
    else:
        # Default sorting by date descending
        base_query = base_query.order_by(desc(MovieModel.date))

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    result_count = await db.execute(count_query)
    total_items = result_count.scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Apply pagination
    base_query = base_query.offset(offset).limit(per_page)

    # Execute query
    result_movies = await db.execute(base_query)
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
