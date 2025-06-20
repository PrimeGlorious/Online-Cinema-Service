from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from database.models.accounts import UserProfileModel, UserModel
from schemas.profiles import UserProfileCreate, UserProfileUpdate
from typing import List


async def get_own_profile(db: AsyncSession, current_user: UserModel):
    profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


async def create_own_profile(
    db: AsyncSession,
    current_user: UserModel,
    profile_in: UserProfileCreate,
) -> UserProfileModel:
    existing = await db.execute(
        select(UserProfileModel)
        .where(UserProfileModel.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profile already exists")

    obj = UserProfileModel(**profile_in.dict(), user_id=current_user.id)

    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return obj


async def update_own_profile(db: AsyncSession, current_user: UserModel, profile_in: UserProfileUpdate):
    profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    async with db.begin():
        db.add(profile)
    await db.refresh(profile)
    return profile


async def get_profile_by_id(db: AsyncSession, profile_id: int, current_user: UserModel):
    profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin" and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return profile


async def update_profile_by_id(
        db: AsyncSession,
        profile_id: int,
        profile_in: UserProfileUpdate,
        current_user: UserModel
):
    profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin" and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    async with db.begin():
        db.add(profile)
    await db.refresh(profile)
    return profile


async def delete_profile_by_id(db: AsyncSession, profile_id: int, current_user: UserModel):
    profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == profile_id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user.group.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    async with db.begin():
        await db.delete(profile)
    return


async def get_all_profiles(db: AsyncSession, current_user: UserModel):
    if current_user.group.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(UserProfileModel))
    profiles = result.scalars().all()
    return profiles
