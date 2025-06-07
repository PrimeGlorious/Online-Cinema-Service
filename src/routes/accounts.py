from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, UserModel, UserGroupModel, UserGroupEnum, ActivationTokenModel

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Registers a new user, assigns them to the USER group, creates an activation token,
    and sends an activation email. Returns the created user's info.

    If the email is already registered, returns 409 Conflict.
    If the USER group is not found, returns 500 Internal Server Error.
    """
)
async def register_user(
        user_data: UserRegistrationRequestSchema,
        db: AsyncSession = Depends(get_db),
):
    """
    Endpoint for user registration.

    - Checks for existing user by email.
    - Retrieves the default USER group.
    - Creates a new user and activation token in a single transaction.
    - Sends an activation email after successful commit.

    Args:
        user_data (UserRegistrationRequestSchema): Registration input (email, password).
        db (AsyncSession): Asynchronous database session dependency.
    Returns:
        UserRegistrationResponseSchema: Info about the created user.
    Raises:
        HTTPException: 409 if email already exists, 500 if user group not found.
    """
    # Check for existing user
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    # Get group_id for USER group
    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalar_one_or_none()
    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found.",
        )

    # Transaction: create user and activation token together
    async with db.begin():
        user = UserModel(email=user_data.email, group_id=user_group.id)
        user.password = user_data.password
        db.add(user)
        await db.flush()

        # Create activation token
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        activation_token = ActivationTokenModel(
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(activation_token)

    await db.refresh(user)

    # Send email after commit, so user is definitely created
    await send_activation_email(email=user.email, token=token) # noqa F821

    return UserRegistrationResponseSchema.model_validate(user)
