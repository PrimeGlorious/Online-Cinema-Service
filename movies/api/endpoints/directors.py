from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db, require_moderator
from movies.models import User

router = APIRouter(prefix="/directors", tags=["directors"])


@router.post("/", response_model=schemas.DirectorRead, status_code=status.HTTP_201_CREATED)
def create_director(
    director: schemas.DirectorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """
    Create a new director.

    Only accessible by users with moderator privileges.
    """
    return crud.create_director(db, director)


@router.get("/", response_model=List[schemas.DirectorRead])
def read_directors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of directors with pagination.

    :param skip: Number of records to skip.
    :param limit: Maximum number of records to return.
    """
    return crud.get_directors(db, skip=skip, limit=limit)


@router.get("/{director_id}", response_model=schemas.DirectorRead)
def read_director(director_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a director by ID.

    Raises 404 error if the director is not found.
    """
    db_director = crud.get_director(db, director_id)
    if not db_director:
        raise HTTPException(status_code=404, detail="Director not found")
    return db_director


@router.put("/{director_id}", response_model=schemas.DirectorRead)
def update_director(
    director_id: int,
    director_update: schemas.DirectorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """
    Update an existing director by ID.

    Only accessible by users with moderator privileges.
    Raises 404 error if the director is not found.
    """
    db_director = crud.update_director(db, director_id, director_update)
    if not db_director:
        raise HTTPException(status_code=404, detail="Director not found")
    return db_director


@router.delete("/{director_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_director(
    director_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """
    Delete a director by ID.

    Only accessible by users with moderator privileges.
    Raises 404 error if the director is not found.
    """
    deleted = crud.delete_director(db, director_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Director not found")
