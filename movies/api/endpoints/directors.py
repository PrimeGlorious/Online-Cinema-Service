from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db

router = APIRouter(prefix="/directors", tags=["directors"])


@router.post("/", response_model=schemas.DirectorRead, status_code=status.HTTP_201_CREATED)
def create_director(director: schemas.DirectorCreate, db: Session = Depends(get_db)):
    db_director = crud.create_director(db, director)
    return db_director


@router.get("/", response_model=List[schemas.DirectorRead])
def read_directors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    directors = crud.get_directors(db, skip=skip, limit=limit)
    return directors


@router.get("/{director_id}", response_model=schemas.DirectorRead)
def read_director(director_id: int, db: Session = Depends(get_db)):
    db_director = crud.get_director(db, director_id)
    if not db_director:
        raise HTTPException(status_code=404, detail="Director not found")
    return db_director
