from fastapi import Depends, Request, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db, UserGroupEnum
from security.http import get_token
from security.token_manager import JWTAuthManager


async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTAuthManager = Depends(get_jwt_auth_manager)
) -> UserModel:
    """
    Dependency that extracts and validates the current user from the JWT access token in the request.

    1. Extracts the Bearer token from the request headers.
    2. Decodes and validates the access token using the JWT manager.
    3. Retrieves the user from the database by user ID from the token payload.
    4. Raises HTTP 401 if the token is invalid, user is not found, or user is inactive.

    Args:
        request (Request): FastAPI request object.
        db (AsyncSession): Async SQLAlchemy session dependency.
        jwt_manager (JWTAuthManager): Dependency for managing JWT tokens.

    Returns:
        UserModel: The current active user.

    Raises:
        HTTPException: If the token is missing, invalid, expired, or the user is not found or inactive.
    """
    # Extract the token from the request
    try:
        token = get_token(request)
    except HTTPException:
        raise

    # Decode the access token
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user id not found"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Query the user from the database
    result = await db.execute(select(UserModel).where(UserModel.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


def require_admin(
        current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency to ensure that the current user is an admin.
    Raises HTTP 403 if not.
    """
    if current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user


def require_moderator(
        current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency to ensure that the current user is a moderator or admin.
    Raises HTTP 403 if not.
    """
    if current_user.group.name not in [UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin privileges required."
        )
    return current_user
