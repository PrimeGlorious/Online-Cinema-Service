from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import get_jwt_auth_manager
from database import get_db, UserModel, UserGroupModel, UserGroupEnum, ActivationTokenModel, RefreshTokenModel

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema, EmailRequestSchema, \
    UserLoginResponseSchema, UserLoginRequestSchema, TokenRefreshResponseSchema, TokenRefreshRequestSchema, \
    LogoutRequestSchema
from tasks.emails import send_activation_email_task, send_activation_complete_email_task

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


@router.get("/activate/{token}/")
async def activate_account(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ActivationTokenModel)
        .options(selectinload(ActivationTokenModel.user))
        .filter(ActivationTokenModel.token == token)
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation link"
        )

    # Activate the user and delete the activation token
    user = record.user
    user.is_active = True
    await db.delete(record)
    await db.commit()

    login_link = "http://localhost:8000/api/v1/accounts/login"
    send_activation_complete_email_task.delay(user.email, login_link)

    return {"message": "Account activated successfully"}


@router.post("/resend-activation/", status_code=status.HTTP_200_OK)
async def resend_activation(
    data: EmailRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    # Find the user
    stmt = select(UserModel).where(UserModel.email == data.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or already active")

    # Delete old activation tokens
    await db.execute(
        delete(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id)
    )
    await db.commit()

    # Create a new activation token
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    activation_token = ActivationTokenModel(
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(activation_token)
    await db.flush()
    await db.commit()

    # Send activation email with the new link
    link = f"http://localhost:8000/api/v1/accounts/activate/{activation_token.token}/"
    send_activation_email_task.delay(user.email, link)

    return {"message": "New activation link sent"}


@router.post("/login/", response_model=UserLoginResponseSchema)
async def login(
    data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
):
    # Find the user by email
    stmt = select(UserModel).where(UserModel.email == data.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or user is not active"
        )

    # Verify password
    if not user.verify_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate access and refresh tokens
    payload = {"sub": str(user.id), "user_id": user.id}
    access_token = jwt_manager.create_access_token(payload)
    refresh_token = jwt_manager.create_refresh_token(payload)

    # Store refresh token in the database
    refresh_token_obj = RefreshTokenModel.create(
        user_id=user.id,
        days_valid=7,
        token=refresh_token
    )
    db.add(refresh_token_obj)
    await db.commit()

    return UserLoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/token/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_token(
    data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
):
    # Find the refresh token in the database
    stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == data.refresh_token)
    result = await db.execute(stmt)
    refresh_token_obj = result.scalar_one_or_none()
    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if the token is expired
    now = datetime.now(timezone.utc)
    if refresh_token_obj.expires_at < now:
        await db.delete(refresh_token_obj)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Find the user
    user = (await db.execute(select(UserModel).where(UserModel.id == refresh_token_obj.user_id))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found"
        )

    # Delete the old refresh token, create a new one, commit
    await db.delete(refresh_token_obj)

    payload = {"sub": str(user.id), "user_id": user.id}
    access_token = jwt_manager.create_access_token(payload)
    new_refresh_token = jwt_manager.create_refresh_token(payload)
    days_valid = 7

    refresh_token_db = RefreshTokenModel.create(
        user_id=user.id,
        days_valid=days_valid,
        token=new_refresh_token
    )
    db.add(refresh_token_db)
    await db.commit()

    return TokenRefreshResponseSchema(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout/", status_code=204)
async def logout(
    data: LogoutRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    # Find the refresh token in the database
    stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == data.refresh_token)
    result = await db.execute(stmt)
    refresh_token_obj = result.scalar_one_or_none()

    # If not found, just return 204 (do not reveal token existence)
    if not refresh_token_obj:
        return

    # Delete the token and commit changes
    await db.delete(refresh_token_obj)
    await db.commit()
    return
