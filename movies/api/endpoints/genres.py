from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db

router = APIRouter(prefix="/genres", tags=["genres"])


@router.post("/", response_model=schemas.GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(genre: schemas.GenreCreate, db: Session = Depends(get_db)):
    db_genre = crud.create_genre(db, genre)
    return db_genre


@router.get("/", response_model=List[schemas.GenreRead])
def read_genres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    genres = crud.get_genres(db, skip=skip, limit=limit)
    return genres


@router.get("/{genre_id}", response_model=schemas.GenreRead)
def read_genre(genre_id: int, db: Session = Depends(get_db)):
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return db_genre
