from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from movies.schemas import MovieCreate, MovieRead, MovieUpdate
from movies.crud import movie_crud
from movies.api.endpoints.dependencies import get_async_session, get_current_active_user, require_moderator
from movies.services import add_movie_rating, toggle_favorite
from movies.models import User

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=List[MovieRead])
async def get_movies(
    genre: Optional[str] = None,
    director: Optional[str] = None,
    star: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by title or description"),
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
):
    return await movie_crud.get_movies(session, genre, director, star, search, skip, limit)


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


@router.post("/{movie_id}/rate", response_model=MovieRead)
async def rate_movie(
    movie_id: int,
    rating: int = Query(..., ge=1, le=10),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await add_movie_rating(session, movie_id, user.id, rating)


@router.post("/{movie_id}/favorite", response_model=MovieRead)
async def toggle_fav(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_active_user),
):
    return await toggle_favorite(session, movie_id, user.id)
