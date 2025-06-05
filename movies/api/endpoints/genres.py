from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from movies import crud, schemas
from movies.api.dependencies import get_db

router = APIRouter(prefix="/genres", tags=["genres"])


@router.post("/", response_model=schemas.GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(genre: schemas.GenreCreate, db: Session = Depends(get_db)):
    """
    Create a new genre.

    Args:
        genre (GenreCreate): Genre data to create.
        db (Session): Database session.

    Returns:
        GenreRead: Created genre.
    """
    db_genre = crud.create_genre(db, genre)
    return db_genre


@router.get("/", response_model=List[schemas.GenreRead])
def read_genres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of genres with pagination.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        db (Session): Database session.

    Returns:
        List[GenreRead]: List of genres.
    """
    genres = crud.get_genres(db, skip=skip, limit=limit)
    return genres


@router.get("/{genre_id}", response_model=schemas.GenreRead)
def read_genre(genre_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a genre by ID.

    Args:
        genre_id (int): Genre ID.
        db (Session): Database session.

    Raises:
        HTTPException: If genre not found.

    Returns:
        GenreRead: Genre data.
    """
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return db_genre


@router.put("/{genre_id}", response_model=schemas.GenreRead)
def update_genre(genre_id: int, genre: schemas.GenreUpdate, db: Session = Depends(get_db)):
    """
    Update a genre by ID.

    Args:
        genre_id (int): Genre ID.
        genre (GenreUpdate): Genre update data.
        db (Session): Database session.

    Raises:
        HTTPException: If genre not found.

    Returns:
        GenreRead: Updated genre data.
    """
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    updated_genre = crud.update_genre(db, db_genre, genre)
    return updated_genre


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(genre_id: int, db: Session = Depends(get_db)):
    """
    Delete a genre by ID.

    Args:
        genre_id (int): Genre ID.
        db (Session): Database session.

    Raises:
        HTTPException: If genre not found.

    Returns:
        None
    """
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    crud.delete_genre(db, db_genre)
    return None


@router.get("/{genre_id}/movies", response_model=List[schemas.MovieRead])
def read_movies_by_genre(genre_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all movies associated with a genre by genre ID.

    Args:
        genre_id (int): Genre ID.
        db (Session): Database session.

    Raises:
        HTTPException: If genre not found.

    Returns:
        List[MovieRead]: List of movies for the given genre.
    """
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    movies = crud.get_movies_by_genre(db, genre_id)
    return movies
