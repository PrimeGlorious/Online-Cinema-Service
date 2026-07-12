from fastapi import Depends, Path, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.dependencies.custom import get_current_user
from database import get_db, UserModel

from crud.comments import get_movie_comments, create_movie_comment, delete_movie_comment
from schemas.comments import MovieCommentResponseSchema, MovieCommentCreateSchema


router = APIRouter()


@router.post(
    "/{movie_id}/",
    response_model=MovieCommentResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_comment(
    movie_id: int = Path(..., ge=1),
    data: MovieCommentCreateSchema = Depends(),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)
):
    """
    Create a comment for a movie.

    Args:
        movie_id (int): ID of the movie.
        data (MovieCommentCreateSchema): Comment creation data.
        db (AsyncSession): Async database session.
        user (UserModel): Current authenticated user.

    Returns:
        MovieCommentResponseSchema: Created comment instance.

    Raises:
        HTTPException: If movie does not exist or creation fails.
    """
    return await create_movie_comment(db, user.id, movie_id, data)


@router.delete(
    "/{comment_id}/",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def remove_comment(
    comment_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)
):
    """
    Delete a movie comment by ID.

    Only the author, moderator, or admin can delete the comment.

    Args:
        comment_id (int): Comment ID to delete.
        db (AsyncSession): Async database session.
        user (UserModel): Current authenticated user.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If comment is not found or user is not authorized.
    """
    return await delete_movie_comment(db, user, comment_id)


@router.get(
    "/{movie_id}/",
    response_model=list[MovieCommentResponseSchema],
    status_code=status.HTTP_200_OK
)
async def list_comments(
    movie_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all comments for a given movie.

    Args:
        movie_id (int): ID of the movie.
        db (AsyncSession): Async database session.

    Returns:
        list[MovieCommentResponseSchema]: List of comments for the movie.
    """
    return await get_movie_comments(db, movie_id)
