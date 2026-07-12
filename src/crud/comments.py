from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from database import UserGroupEnum, UserModel
from database.models.movies import MovieCommentModel
from schemas.comments import MovieCommentCreateSchema, MovieCommentResponseSchema


async def create_movie_comment(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    data: MovieCommentCreateSchema
) -> MovieCommentModel:
    """
    Create a comment for a specific movie.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): User ID creating the comment.
        movie_id (int): ID of the movie.
        data (MovieCommentCreateSchema): Comment creation data.

    Returns:
        MovieCommentModel: Created comment instance.
    """
    comment = MovieCommentModel(
        user_id=user_id,
        movie_id=movie_id,
        content=data.content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_movie_comment(
    db: AsyncSession,
    user: UserModel,
    comment_id: int
) -> dict:
    """
    Delete a comment by ID if the user is the author, moderator, or admin.

    Args:
        db (AsyncSession): Async database session.
        user (UserModel): Current authenticated user.
        comment_id (int): Comment ID to delete.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If comment is not found or user is not authorized.
    """
    result = await db.execute(
        select(MovieCommentModel).where(MovieCommentModel.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    user_group = getattr(user.group, "name", None)
    if not (
        comment.user_id == user.id
        or user_group == UserGroupEnum.ADMIN
        or user_group == UserGroupEnum.MODERATOR
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    await db.delete(comment)
    await db.commit()
    return {"detail": "Comment deleted successfully"}


async def get_movie_comments(
    db: AsyncSession,
    movie_id: int
) -> list[MovieCommentResponseSchema]:
    """
    Retrieve comments for a specific movie.

    Args:
        db (AsyncSession): Async database session.
        movie_id (int): ID of the movie.

    Returns:
        list[MovieCommentResponseSchema]: List of comments for the movie.
    """
    result = await db.execute(
        select(MovieCommentModel).where(MovieCommentModel.movie_id == movie_id)
    )
    comments = result.scalars().all()
    return [MovieCommentResponseSchema.model_validate(comment) for comment in comments]
