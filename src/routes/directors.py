from typing import List, Optional
from fastapi import Query, Depends, Request, APIRouter, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db, DirectorModel  # Твоя модель DirectorModel має бути імпортована
from schemas.directors import (
    DirectorListResponseSchema,
    DirectorListItemSchema,
    DirectorCreateSchema,
    DirectorUpdateSchema,
    DirectorResponseSchema,
)

router = APIRouter()


@router.get(
    "/directors/",
    response_model=DirectorListResponseSchema,
    summary="Get a paginated list of directors",
    description=(
        "Retrieve a paginated list of directors."
    ),
    responses={
        404: {
            "description": "No directors found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No directors found."}
                }
            },
        }
    }
)
async def get_director_list(
        request: Request,
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
        db: AsyncSession = Depends(get_db),
) -> DirectorListResponseSchema:
    stmt = select(DirectorModel).offset((page - 1) * per_page).limit(per_page)
    count_stmt = select(func.count()).select_from(DirectorModel)

    result = await db.execute(stmt)
    directors = result.scalars().all()

    if not directors:
        raise HTTPException(status_code=404, detail="No directors found.")

    total_result = await db.execute(count_stmt)
    total_items = total_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    base_url = str(request.url.replace_query_params())
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return DirectorListResponseSchema(
        directors=[DirectorListItemSchema.model_validate(d) for d in directors],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post(
    "/directors/",
    response_model=DirectorResponseSchema,
    summary="Add a new director",
    status_code=201,
    responses={
        201: {"description": "Director created successfully."},
        400: {"description": "Invalid input data."},
        409: {"description": "Director with the same name already exists."}
    },
)
async def create_director(
        director_data: DirectorCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> DirectorResponseSchema:
    stmt = select(DirectorModel).where(DirectorModel.name == director_data.name)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Director with this name already exists.")

    director = DirectorModel(name=director_data.name)
    db.add(director)
    try:
        await db.commit()
        await db.refresh(director)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return DirectorResponseSchema.model_validate(director)


@router.get(
    "/directors/{director_id}/",
    response_model=DirectorResponseSchema,
    summary="Get director details by ID",
    responses={
        404: {"description": "Director not found."}
    }
)
async def get_director_by_id(
        director_id: int,
        db: AsyncSession = Depends(get_db)
) -> DirectorResponseSchema:
    stmt = select(DirectorModel).where(DirectorModel.id == director_id)
    result = await db.execute(stmt)
    director = result.scalars().first()
    if not director:
        raise HTTPException(status_code=404, detail="Director not found.")
    return DirectorResponseSchema.model_validate(director)


@router.patch(
    "/directors/{director_id}/",
    response_model=DirectorResponseSchema,
    summary="Update a director by ID",
    responses={
        200: {"description": "Director updated successfully."},
        404: {"description": "Director not found."},
        400: {"description": "Invalid input data."}
    }
)
async def update_director(
        director_id: int,
        director_data: DirectorUpdateSchema,
        db: AsyncSession = Depends(get_db)
) -> DirectorResponseSchema:
    stmt = select(DirectorModel).where(DirectorModel.id == director_id)
    result = await db.execute(stmt)
    director = result.scalars().first()
    if not director:
        raise HTTPException(status_code=404, detail="Director not found.")

    for field, value in director_data.model_dump(exclude_unset=True).items():
        setattr(director, field, value)

    try:
        await db.commit()
        await db.refresh(director)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return DirectorResponseSchema.model_validate(director)


@router.delete(
    "/directors/{director_id}/",
    status_code=204,
    summary="Delete a director by ID",
    responses={
        204: {"description": "Director deleted successfully."},
        404: {"description": "Director not found."}
    }
)
async def delete_director(
        director_id: int,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(DirectorModel).where(DirectorModel.id == director_id)
    result = await db.execute(stmt)
    director = result.scalars().first()
    if not director:
        raise HTTPException(status_code=404, detail="Director not found.")

    await db.delete(director)
    await db.commit()
    return None
