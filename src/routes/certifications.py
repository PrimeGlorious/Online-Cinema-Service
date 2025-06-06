from fastapi import APIRouter, Depends, Query, Request, HTTPException

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db, CertificationModel
from schemas.certifications import (
    CertificationCreateSchema,
    CertificationUpdateSchema,
    CertificationListResponseSchema,
    CertificationListItemSchema,
)

router = APIRouter()


@router.get(
    "/certifications/",
    response_model=CertificationListResponseSchema,
    summary="Get a paginated list of certifications",
    description=(
        "<h3>Retrieve a paginated list of certifications from the database.</h3>"
    ),
    responses={
        404: {
            "description": "No certifications found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No certifications found."}
                }
            },
        }
    }
)
async def get_certification_list(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> CertificationListResponseSchema:
    stmt = select(CertificationModel).order_by(CertificationModel.id)
    total_result = await db.execute(select(func.count()).select_from(CertificationModel))
    total_items = total_result.scalar_one()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No certifications found.")

    offset = (page - 1) * per_page
    result = await db.execute(stmt.offset(offset).limit(per_page))
    certifications = result.scalars().all()

    total_pages = (total_items + per_page - 1) // per_page

    base_url = str(request.url).split("?")[0]
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return CertificationListResponseSchema(
        certifications=certifications,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/certifications/",
    response_model=CertificationListItemSchema,
    summary="Create a new certification",
    description=(
        "<h3>Create a new certification entry.</h3>"
    ),
    status_code=201,
    responses={
        400: {
            "description": "Invalid input data.",
            "content": {"application/json": {"example": {"detail": "Invalid input data."}}},
        },
        409: {
            "description": "Certification with this name already exists.",
            "content": {"application/json": {"example": {"detail": "Certification already exists."}}},
        },
    },
)
async def create_certification(
    certification_data: CertificationCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> CertificationListItemSchema:
    stmt = select(CertificationModel).where(CertificationModel.name == certification_data.name)
    result = await db.execute(stmt)
    existing_cert = result.scalars().first()
    if existing_cert:
        raise HTTPException(status_code=409, detail="Certification with this name already exists.")

    cert = CertificationModel(name=certification_data.name)
    db.add(cert)
    try:
        await db.commit()
        await db.refresh(cert)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return CertificationListItemSchema.model_validate(cert)


@router.get(
    "/certifications/{certification_id}/",
    response_model=CertificationListItemSchema,
    summary="Get certification by ID",
    description=(
        "<h3>Fetch certification details by its ID.</h3>"
    ),
    responses={
        404: {
            "description": "Certification not found.",
            "content": {"application/json": {"example": {"detail": "Certification not found."}}},
        }
    }
)
async def get_certification_by_id(
    certification_id: int,
    db: AsyncSession = Depends(get_db),
) -> CertificationListItemSchema:
    stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found.")

    return CertificationListItemSchema.model_validate(cert)


@router.delete(
    "/certifications/{certification_id}/",
    summary="Delete certification by ID",
    description="<h3>Delete a certification by its ID.</h3>",
    status_code=204,
    responses={
        404: {
            "description": "Certification not found.",
            "content": {"application/json": {"example": {"detail": "Certification not found."}}},
        }
    }
)
async def delete_certification(
    certification_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found.")

    await db.delete(cert)
    await db.commit()
    return {"detail": "Certification deleted successfully."}


@router.patch(
    "/certifications/{certification_id}/",
    summary="Update certification by ID",
    description="<h3>Update a certification by its ID.</h3>",
    responses={
        200: {"description": "Certification updated successfully."},
        404: {
            "description": "Certification not found.",
            "content": {"application/json": {"example": {"detail": "Certification not found."}}},
        },
        400: {
            "description": "Invalid input data.",
            "content": {"application/json": {"example": {"detail": "Invalid input data."}}},
        },
    }
)
async def update_certification(
    certification_id: int,
    certification_data: CertificationUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found.")

    for field, value in certification_data.model_dump(exclude_unset=True).items():
        setattr(cert, field, value)

    try:
        await db.commit()
        await db.refresh(cert)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Certification updated successfully."}
