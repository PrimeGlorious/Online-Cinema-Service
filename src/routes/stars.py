from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from database import get_db
from database.models.movies import StarModel
from schemas.stars import (
    StarCreateSchema,
    StarUpdateSchema,
    StarListItemSchema,
    StarListResponseSchema,
    StarDetailSchema
)

router = APIRouter(prefix="/stars", tags=["Stars"])

@router.get("/", response_model=StarListResponseSchema)
async def list_stars(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch a paginated list of stars from the database (asynchronously).

    Retrieves a list of stars based on the provided page number and number of items per page.
    Returns metadata including total item count and navigation links to previous/next pages.

    :param page: The page number to retrieve (1-based index, must be >= 1).
    :type page: int
    :param per_page: The number of items per page (between 1 and 50).
    :type per_page: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Paginated list of stars with total count and navigation links.
    :rtype: StarListResponseSchema

    :raises HTTPException: 404 error if no stars are found.
    """
    offset = (page - 1) * per_page

    count_stmt = select(func.count(StarModel.id))
    total_items = (await db.execute(count_stmt)).scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No stars found.")

    stmt = select(StarModel).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    stars = result.scalars().all()

    if not stars:
        raise HTTPException(status_code=404, detail="No stars found.")

    return StarListResponseSchema(
        stars=[StarListItemSchema.model_validate(star) for star in stars],
        total_items=total_items,
        total_pages=(total_items + per_page - 1) // per_page,
        prev_page=f"/stars/?page={page-1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/stars/?page={page+1}&per_page={per_page}" if page * per_page < total_items else None
    )


@router.get("/{star_id}/", response_model=StarDetailSchema)
async def get_star(star_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a single star by its ID from the database.

    :param star_id: Unique ID of the star to retrieve.
    :type star_id: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Detailed information about the requested star.
    :rtype: StarDetailSchema

    :raises HTTPException: 404 error if the star is not found.
    """
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    return StarDetailSchema.model_validate(star)


@router.post("/", response_model=StarDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_star(star_in: StarCreateSchema, db: AsyncSession = Depends(get_db)):
    """
    Create a new star in the database.

    :param star_in: Data required to create a new star.
    :type star_in: StarCreateSchema
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Detailed data of the newly created star.
    :rtype: StarDetailSchema

    :raises HTTPException: 400 error if a star with the same name already exists.
    """
    new_star = StarModel(name=star_in.name)
    db.add(new_star)
    try:
        await db.commit()
        await db.refresh(new_star)
        return StarDetailSchema.model_validate(new_star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Star with this name already exists.")


@router.put("/{star_id}/", response_model=StarDetailSchema)
async def update_star(star_id: int, star_in: StarUpdateSchema, db: AsyncSession = Depends(get_db)):
    """
    Update an existing star's information.

    :param star_id: Unique ID of the star to update.
    :type star_id: int
    :param star_in: Updated star data.
    :type star_in: StarUpdateSchema
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: Updated detailed data of the star.
    :rtype: StarDetailSchema

    :raises HTTPException: 404 error if the star is not found.
    :raises HTTPException: 400 error if a star with the new name already exists.
    """
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")

    star.name = star_in.name
    try:
        await db.commit()
        await db.refresh(star)
        return StarDetailSchema.model_validate(star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Star with this name already exists.")


@router.delete("/{star_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a star from the database by its ID.

    :param star_id: Unique ID of the star to delete.
    :type star_id: int
    :param db: Asynchronous SQLAlchemy session for DB interaction.
    :type db: AsyncSession

    :return: None
    :rtype: None

    :raises HTTPException: 404 error if the star is not found.
    """
    star = await db.get(StarModel, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    await db.delete(star)
    await db.commit()
