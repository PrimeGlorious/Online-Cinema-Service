from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, UserModel, UserGroupModel, UserGroupEnum, ActivationTokenModel

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema
from tasks.emails import send_activation_email_task

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Creates a new user account with the provided email and password.
    \n    - Checks if the email is already registered (returns 409 Conflict if so).
    - Retrieves or seeds the default USER group.
    - Stores the user and activation token in a single transaction.
    - Sends an activation email with a 24-hour expiry link.
    """
)
async def register_user(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> UserRegistrationResponseSchema:
    """
    Register endpoint logic:

    1. Verify that the email is not already in use.
    2. Obtain or create the default 'USER' group and get its ID.
    3. Create the UserModel instance and hash the password.
    4. Create an ActivationTokenModel for email verification.
    5. Commit all changes atomically.
    6. Refresh and return the new user.

    Args:
        user_data: Pydantic schema containing 'email' and 'password'.
        db: AsyncSession dependency for database operations.
    Returns:
        UserRegistrationResponseSchema: Newly created user data.
    Raises:
        HTTPException(409): If a user with the given email already exists.
        HTTPException(500): If for any reason the default USER group cannot be found or created.
    """
    # 1) Check for existing user by email
    existing = await db.scalar(
        select(UserModel.id).where(UserModel.email == user_data.email)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    # 2) Retrieve or seed default USER group
    default_group_id = await db.scalar(
        select(UserGroupModel.id).where(UserGroupModel.name == UserGroupEnum.USER)
    )
    if default_group_id is None:
        new_group = UserGroupModel(name=UserGroupEnum.USER)
        db.add(new_group)
        await db.flush()  # populate new_group.id
        default_group_id = new_group.id

    # 3) Create UserModel and hash password
    user = UserModel(
        email=user_data.email,
        group_id=default_group_id,
    )
    user.password = user_data.password
    db.add(user)
    await db.flush()  # populate user.id

    # 4) Create activation token valid for 24 hours
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    activation_token = ActivationTokenModel(
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(activation_token)

    # 5) Commit all operations atomically
    await db.commit()

    # 6) Refresh to load relationships
    await db.refresh(user)

    # 7) Trigger sending of activation email asynchronously
    activation_link = f"http://localhost:8000/api/v1/accounts/activate/{activation_token.token}/"
    print("CALL SEND_ACTIVATION_EMAIL_TASK", send_activation_email_task)
    send_activation_email_task.delay(
        user.email,
        activation_link,
    )

    return UserRegistrationResponseSchema.model_validate(user)
