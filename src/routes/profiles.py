from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.dependencies.custom import get_current_user, get_db
from database.models.accounts import UserModel, UserProfileModel
from schemas.profiles import UserProfileCreate, UserProfileUpdate, UserProfileRead, UserProfileOut
from crud.profiles import (
    get_own_profile, create_own_profile, update_own_profile,
    get_profile_by_id, update_profile_by_id, delete_profile_by_id, get_all_profiles
)
from typing import List

router = APIRouter()


@router.get("/me", response_model=UserProfileOut)
async def read_own_profile(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(UserProfileModel)
        .where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/", response_model=UserProfileRead)
async def create_my_profile(
    profile_in: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await create_own_profile(db, current_user, profile_in)


@router.patch("/me", response_model=UserProfileRead)
async def update_my_profile(
    profile_in: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await update_own_profile(db, current_user, profile_in)


@router.get("/", response_model=List[UserProfileRead])
async def get_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await get_all_profiles(db, current_user)


@router.get("/{profile_id}", response_model=UserProfileRead)
async def get_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await get_profile_by_id(db, profile_id, current_user)


@router.patch("/{profile_id}", response_model=UserProfileRead)
async def update_profile(
    profile_id: int,
    profile_in: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await update_profile_by_id(db, profile_id, profile_in, current_user)


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    await delete_profile_by_id(db, profile_id, current_user)
    return {"detail": "Profile deleted"}
