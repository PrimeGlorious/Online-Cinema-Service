from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from movies.schemas import (
    MovieCreate,
    MovieRead,
    MovieUpdate,
    GenreCreate,
    GenreRead,
    StarCreate,
    StarRead,
    MovieCommentCreate,
    MovieComment,
    MovieRatingCreate,
    MovieFavoriteCreate,
)
from movies.crud import (
    movie_crud,
    genre_crud,
    star_crud,
    comment_crud,
    rating_crud,
    favorite_crud,
)
from movies.api.endpoints.dependencies import (
    get_async_session,
    get_current_active_user,
    require_moderator,
)
from movies.models import User

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=List[MovieRead])
async def get_movies(
    genre: Optional[str] = None,
    director: Optional[str] = None,
    star: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by title or description"),
    sort_by: Optional[str] = Query(None, description="Sort by attribute"),
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
):
    return await movie_crud.get_movies(
        session, genre, director, star, search, sort_by, skip, limit
    )


@router.post("/", response_model=MovieRead)
async def create_movie(
    movie_in: MovieCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_moderator),
):
    return await movie_crud.create_movie(session, movie_in)


@router.get("/{movie_id}", response_model=MovieRead)
async def get_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    movie = await movie_crud.get_movie(session, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.put("/{movie_id}", response_model=MovieRead)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_moderator),
):
    movie = await movie_crud.update_movie(session, movie_id, movie_in)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_moderator),
):
    deleted = await movie_crud.delete_movie(session, movie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Movie not found")


@router.post("/{movie_id}/like", response_model=MovieRead)
async def like_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await movie_crud.like_movie(session, movie_id, user.id)


@router.post("/{movie_id}/dislike", response_model=MovieRead)
async def dislike_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await movie_crud.dislike_movie(session, movie_id, user.id)


@router.post("/{movie_id}/comment", response_model=MovieComment)
async def comment_movie(
    movie_id: int,
    comment_in: MovieCommentCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await comment_crud.create_comment(session, movie_id, user.id, comment_in)


@router.post("/{movie_id}/rate", response_model=MovieRead)
async def rate_movie(
    movie_id: int,
    rating_in: MovieRatingCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await rating_crud.add_rating(session, movie_id, user.id, rating_in)


@router.post("/{movie_id}/favorite", response_model=MovieRead)
async def add_to_favorites(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await favorite_crud.add_to_favorites(session, movie_id, user.id)


@router.delete("/{movie_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    removed = await favorite_crud.remove_from_favorites(session, movie_id, user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorite not found")


@router.get("/genres", response_model=List[GenreRead])
async def get_genres(
    session: AsyncSession = Depends(get_async_session),
):
    return await genre_crud.get_genres_with_counts(session)


@router.post("/genres", response_model=GenreRead)
async def create_genre(
    genre_in: GenreCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_moderator),
):
    return await genre_crud.create_genre(session, genre_in)


@router.get("/stars", response_model=List[StarRead])
async def get_stars(
    session: AsyncSession = Depends(get_async_session),
):
    return await star_crud.get_stars(session)


@router.post("/stars", response_model=StarRead)
async def create_star(
    star_in: StarCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_moderator),
):
    return await star_crud.create_star(session, star_in)
