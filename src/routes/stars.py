from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db, StarModel
from schemas.stars import (
    StarCreateSchema,
    StarUpdateSchema,
    StarDetailSchema,
    StarListResponseSchema
)

router = APIRouter()


@router.get(
    "/stars/",
    response_model=StarListResponseSchema,
    summary="Retrieve a list of stars with pagination",
    description=(
        "<h3>This endpoint returns a paginated list of stars. "
        "You can specify the page number and the number of items per "
        "page using the `page` and `per_page` query parameters. "
        "The response includes pagination info and links to previous and next pages, if applicable.</h3>"
    ),
    responses={
        404: {
            "description": "No stars found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No stars found."}
                }
            },
        }
    }
)
async def get_star_list(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    per_page: int = Query(10, ge=1, le=50, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
) -> StarListResponseSchema:
    """
    Retrieve a paginated list of stars.

    :param request: FastAPI request object.
    :param page: Page number (starts from 1).
    :param per_page: Number of items per page.
    :param db: Async SQLAlchemy session.

    :return: Paginated response with stars.
    :raises HTTPException 404: If no stars are found.
    """
    offset = (page - 1) * per_page
    stmt = select(StarModel).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    stars = result.scalars().all()

    if not stars:
        raise HTTPException(status_code=404, detail="No stars found.")

    total_stmt = select(func.count()).select_from(StarModel)
    total_result = await db.execute(total_stmt)
    total_items = total_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = f"{request.url.path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{request.url.path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return StarListResponseSchema(
        stars=stars,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post(
    "/stars/",
    response_model=StarDetailSchema,
    summary="Create a new star",
    description=(
        "<h3>This endpoint allows creating a new star by specifying its name. "
        "If a star with the same name already exists, a 409 Conflict error is returned.</h3>"
    ),
    responses={
        201: {"description": "Star successfully created."},
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data."}
                }
            },
        },
        409: {
            "description": "Star with this name already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star with this name already exists."}
                }
            },
        }
    },
    status_code=201
)
async def create_star(
    star_data: StarCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> StarDetailSchema:
    """
    Create a new star.

    :param star_data: Data for the new star.
    :param db: Async SQLAlchemy session.

    :return: Created star details.
    :raises HTTPException 409: If star already exists.
    :raises HTTPException 400: On validation error.
    """
    existing_stmt = select(StarModel).where(StarModel.name == star_data.name)
    existing_result = await db.execute(existing_stmt)
    existing_star = existing_result.scalars().first()

    if existing_star:
        raise HTTPException(
            status_code=409,
            detail=f"Star with name '{star_data.name}' already exists."
        )

    new_star = StarModel(name=star_data.name)
    db.add(new_star)
    try:
        await db.commit()
        await db.refresh(new_star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return StarDetailSchema.model_validate(new_star)


@router.get(
    "/stars/{star_id}/",
    response_model=StarDetailSchema,
    summary="Get details of a specific star",
    description=(
        "<h3>This endpoint returns the details of a star by its ID. "
        "If the star does not exist, a 404 Not Found error is returned.</h3>"
    ),
    responses={
        404: {
            "description": "Star not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star not found."}
                }
            },
        }
    }
)
async def get_star_by_id(
    star_id: int,
    db: AsyncSession = Depends(get_db)
) -> StarDetailSchema:
    """
    Get a star by its ID.

    :param star_id: ID of the star to retrieve.
    :param db: Async SQLAlchemy session.

    :return: Star details.
    :raises HTTPException 404: If star not found.
    """
    stmt = select(StarModel).where(StarModel.id == star_id)
    result = await db.execute(stmt)
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")

    return StarDetailSchema.model_validate(star)


@router.put(
    "/stars/{star_id}/",
    response_model=StarDetailSchema,
    summary="Update an existing star",
    description=(
        "<h3>This endpoint allows updating an existing star by its ID. "
        "If the star is not found, a 404 Not Found error is returned. "
        "If a conflict occurs (e.g. duplicate name), a 409 Conflict error is returned.</h3>"
    ),
    responses={
        200: {"description": "Star successfully updated."},
        404: {"description": "Star not found."},
        409: {"description": "Star with this name already exists."}
    }
)
async def update_star(
    star_id: int,
    star_data: StarUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> StarDetailSchema:
    """
    Update an existing star by ID.

    :param star_id: ID of the star to update.
    :param star_data: New star data.
    :param db: Async SQLAlchemy session.

    :return: Updated star details.
    :raises HTTPException 404: If star not found.
    :raises HTTPException 409: If name already exists.
    """
    stmt = select(StarModel).where(StarModel.id == star_id)
    result = await db.execute(stmt)
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")

    if star_data.name != star.name:
        name_check = await db.execute(select(StarModel).where(StarModel.name == star_data.name))
        if name_check.scalars().first():
            raise HTTPException(
                status_code=409,
                detail=f"Star with name '{star_data.name}' already exists."
            )

    star.name = star_data.name
    try:
        await db.commit()
        await db.refresh(star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Conflict updating star.")

    return StarDetailSchema.model_validate(star)


@router.delete(
    "/stars/{star_id}/",
    status_code=204,
    summary="Delete a star by ID",
    description=(
        "<h3>This endpoint deletes a star by its ID. "
        "If the star is not found, a 404 Not Found error is returned. "
        "If successful, it returns HTTP 204 No Content.</h3>"
    ),
    responses={
        204: {"description": "Star successfully deleted."},
        404: {
            "description": "Star not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star not found."}
                }
            },
        }
    }
)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a star by its ID.

    :param star_id: ID of the star to delete.
    :param db: Async SQLAlchemy session.

    :raises HTTPException 404: If star not found.
    """
    stmt = select(StarModel).where(StarModel.id == star_id)
    result = await db.execute(stmt)
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")

    await db.delete(star)
    await db.commit()
