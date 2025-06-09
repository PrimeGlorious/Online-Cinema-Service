from fastapi import Query, Depends, Request, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from database import get_db

from crud.movies import movie_list
from schemas.movies import (
    MovieListResponseSchema,
    MovieFilterSchema,
    SortField,
    SortOrder
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    summary="Get a paginated list of movies",
    description=(
            "<h3>This endpoint retrieves a paginated list of movies from the database. "
            "Clients can specify the `page` number and the number of items per page using `per_page`. "
            "The response includes details about the movies, total pages, and total items, "
            "along with links to the previous and next pages if applicable.</h3>"
            "<h4>Filtering options:</h4>"
            "<ul>"
            "<li>date_from: Filter movies released from this date</li>"
            "<li>date_to: Filter movies released until this date</li>"
            "<li>score_from: Filter movies with score from</li>"
            "<li>score_to: Filter movies with score to</li>"
            "<li>price_from: Filter movies with price from</li>"
            "<li>price_to: Filter movies with price to</li>"
            "<li>genre: Filter movies by genre</li>"
            "<li>certification: Filter movies by certification</li>"
            "<li>director: Filter movies by director</li>"
            "<li>star: Filter movies by star</li>"
            "<li>search: Search in movie title, description, director, or star names</li>"
            "</ul>"
            "<h4>Sorting options:</h4>"
            "<ul>"
            "<li>sort_by: Field to sort by (date, score, price, votes)</li>"
            "<li>sort_order: Sort order (asc/desc)</li>"
            "</ul>"
    ),
    responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            },
        }
    }
)
async def get_movie_list(
        request: Request,
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        date_from: date = Query(None, description="Filter movies released from this date"),
        date_to: date = Query(None, description="Filter movies released until this date"),
        score_from: float = Query(None, ge=0, le=10, description="Filter movies with score from"),
        score_to: float = Query(None, ge=0, le=10, description="Filter movies with score to"),
        price_from: float = Query(None, ge=0, description="Filter movies with price from"),
        price_to: float = Query(None, ge=0, description="Filter movies with price to"),
        genre: str = Query(None, description="Filter movies by genre"),
        certification: str = Query(None, description="Filter movies by certification"),
        director: str = Query(None, description="Filter movies by director"),
        star: str = Query(None, description="Filter movies by star"),
        search: str = Query(None, description="Search in movie title, description, director, or star names"),
        sort_by: SortField = Query(None, description="Field to sort by"),
        sort_order: SortOrder = Query(None, description="Sort order (asc/desc)"),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    filters = MovieFilterSchema(
        date_from=date_from,
        date_to=date_to,
        score_from=score_from,
        score_to=score_to,
        price_from=price_from,
        price_to=price_to,
        genre=genre,
        certification=certification,
        director=director,
        star=star,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await movie_list(
        request=request,
        db=db,
        page=page,
        per_page=per_page,
        filters=filters
    )
