from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from database.models.accounts import UserProfileModel, UserModel
from schemas.profiles import UserProfileCreate, UserProfileUpdate
from typing import List

async def get_own_profile(db: AsyncSession, current_user: UserModel) -> UserProfileModel:
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

async def create_own_profile(
    db: AsyncSession,
    current_user: UserModel,
    profile_in: UserProfileCreate,
) -> UserProfileModel:
    existing = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profile already exists")

    obj = UserProfileModel(**profile_in.dict(), user_id=current_user.id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def update_own_profile(
    db: AsyncSession,
    current_user: UserModel,
    profile_in: UserProfileUpdate,
) -> UserProfileModel:
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile

async def get_profile_by_id(
    db: AsyncSession,
    profile_id: int,
    current_user: UserModel,
) -> UserProfileModel:
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin" and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return profile

async def update_profile_by_id(
    db: AsyncSession,
    profile_id: int,
    profile_in: UserProfileUpdate,
    current_user: UserModel,
) -> UserProfileModel:
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin" and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile

async def delete_profile_by_id(
    db: AsyncSession,
    profile_id: int,
    current_user: UserModel,
) -> None:
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    await db.delete(profile)
    await db.commit()

async def get_all_profiles(
    db: AsyncSession,
    current_user: UserModel,
) -> List[UserProfileModel]:
    if current_user.group.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(UserProfileModel))
    return result.scalars().all()
