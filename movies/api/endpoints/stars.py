from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db

router = APIRouter(prefix="/stars", tags=["stars"])


@router.post("/", response_model=schemas.StarRead, status_code=status.HTTP_201_CREATED)
def create_star(star: schemas.StarCreate, db: Session = Depends(get_db)):
    """
    Create a new star if it does not exist.

    Args:
        star (schemas.StarCreate): Star data to create.
        db (Session): Database session.

    Raises:
        HTTPException: If a star with the same name already exists.

    Returns:
        schemas.StarRead: Created star data.
    """
    existing_star = crud.get_star_by_name(db, star.name)
    if existing_star:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Star with this name already exists",
        )
    db_star = crud.create_star(db, star)
    return db_star


@router.get("/", response_model=List[schemas.StarRead])
def read_stars(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of stars with pagination.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        db (Session): Database session.

    Returns:
        List[schemas.StarRead]: List of stars.
    """
    stars = crud.get_stars(db, skip=skip, limit=limit)
    return stars


@router.get("/{star_id}", response_model=schemas.StarRead)
def read_star(star_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single star by ID.

    Args:
        star_id (int): ID of the star to retrieve.
        db (Session): Database session.

    Raises:
        HTTPException: If the star is not found.

    Returns:
        schemas.StarRead: Star data.
    """
    db_star = crud.get_star(db, star_id)
    if not db_star:
        raise HTTPException(status_code=404, detail="Star not found")
    return db_star


@router.put("/{star_id}", response_model=schemas.StarRead)
def update_star(star_id: int, star_update: schemas.StarUpdate, db: Session = Depends(get_db)):
    """
    Update an existing star's information.

    Args:
        star_id (int): ID of the star to update.
        star_update (schemas.StarUpdate): Updated star data.
        db (Session): Database session.

    Raises:
        HTTPException: If the star is not found or name conflicts with another star.

    Returns:
        schemas.StarRead: Updated star data.
    """
    db_star = crud.get_star(db, star_id)
    if not db_star:
        raise HTTPException(status_code=404, detail="Star not found")

    if star_update.name and star_update.name != db_star.name:
        existing_star = crud.get_star_by_name(db, star_update.name)
        if existing_star:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Star with this name already exists",
            )

    updated_star = crud.update_star(db, db_star, star_update)
    return updated_star


@router.delete("/{star_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_star(star_id: int, db: Session = Depends(get_db)):
    """
    Delete a star by ID.

    Args:
        star_id (int): ID of the star to delete.
        db (Session): Database session.

    Raises:
        HTTPException: If the star is not found.

    Returns:
        None
    """
    db_star = crud.get_star(db, star_id)
    if not db_star:
        raise HTTPException(status_code=404, detail="Star not found")

    crud.delete_star(db, db_star)
    return None
