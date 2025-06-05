from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db

router = APIRouter(prefix="/stars", tags=["stars"])


@router.post("/", response_model=schemas.StarRead, status_code=status.HTTP_201_CREATED)
def create_star(star: schemas.StarCreate, db: Session = Depends(get_db)):
    db_star = crud.create_star(db, star)
    return db_star


@router.get("/", response_model=List[schemas.StarRead])
def read_stars(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stars = crud.get_stars(db, skip=skip, limit=limit)
    return stars


@router.get("/{star_id}", response_model=schemas.StarRead)
def read_star(star_id: int, db: Session = Depends(get_db)):
    db_star = crud.get_star(db, star_id)
    if not db_star:
        raise HTTPException(status_code=404, detail="Star not found")
    return db_star
