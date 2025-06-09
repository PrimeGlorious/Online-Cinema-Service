from fastapi import Query, Depends, Request, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

from crud.movies import movie_list, movie_create, movie_item
from schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema, MovieCreateSchema

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
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    return await movie_list(
        request=request,
        db=db,
        page=page,
        per_page=per_page
    )


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=201,
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    return await movie_create(
        movie_data=movie_data,
        db=db,
    )
