from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas


# --- Genres ---

def get_genre(db: Session, genre_id: int) -> Optional[models.Genre]:
    return db.query(models.Genre).filter(models.Genre.id == genre_id).first()


def get_genres(db: Session, skip: int = 0, limit: int = 100) -> List[models.Genre]:
    return db.query(models.Genre).offset(skip).limit(limit).all()


def create_genre(db: Session, genre: schemas.GenreCreate) -> models.Genre:
    db_genre = models.Genre(name=genre.name)
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre


# --- Stars ---

def get_star(db: Session, star_id: int) -> Optional[models.Star]:
    return db.query(models.Star).filter(models.Star.id == star_id).first()


def get_stars(db: Session, skip: int = 0, limit: int = 100) -> List[models.Star]:
    return db.query(models.Star).offset(skip).limit(limit).all()


def create_star(db: Session, star: schemas.StarCreate) -> models.Star:
    db_star = models.Star(name=star.name)
    db.add(db_star)
    db.commit()
    db.refresh(db_star)
    return db_star


# --- Directors ---

def get_director(db: Session, director_id: int) -> Optional[models.Director]:
    return db.query(models.Director).filter(models.Director.id == director_id).first()


def get_directors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Director]:
    return db.query(models.Director).offset(skip).limit(limit).all()


def create_director(db: Session, director: schemas.DirectorCreate) -> models.Director:
    db_director = models.Director(name=director.name)
    db.add(db_director)
    db.commit()
    db.refresh(db_director)
    return db_director


# --- Certifications ---

def get_certification(db: Session, certification_id: int) -> Optional[models.Certification]:
    return db.query(models.Certification).filter(models.Certification.id == certification_id).first()


def get_certifications(db: Session, skip: int = 0, limit: int = 100) -> List[models.Certification]:
    return db.query(models.Certification).offset(skip).limit(limit).all()


def create_certification(db: Session, certification: schemas.CertificationCreate) -> models.Certification:
    db_cert = models.Certification(name=certification.name)
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert


# --- Movies ---

def get_movie(db: Session, movie_id: int) -> Optional[models.Movie]:
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()


def get_movie_by_uuid(db: Session, movie_uuid: str) -> Optional[models.Movie]:
    return db.query(models.Movie).filter(models.Movie.uuid == movie_uuid).first()


def get_movies(db: Session, skip: int = 0, limit: int = 100) -> List[models.Movie]:
    return db.query(models.Movie).offset(skip).limit(limit).all()


def create_movie(db: Session, movie: schemas.MovieCreate) -> models.Movie:
    db_movie = models.Movie(
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=movie.price,
        certification_id=movie.certification_id,
    )
    # Add relations
    if movie.genre_ids:
        db_movie.genres = db.query(models.Genre).filter(models.Genre.id.in_(movie.genre_ids)).all()
    if movie.star_ids:
        db_movie.stars = db.query(models.Star).filter(models.Star.id.in_(movie.star_ids)).all()
    if movie.director_ids:
        db_movie.directors = db.query(models.Director).filter(models.Director.id.in_(movie.director_ids)).all()

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


def update_movie(db: Session, movie: models.Movie, movie_update: schemas.MovieUpdate) -> models.Movie:
    for field, value in movie_update.dict(exclude_unset=True).items():
        if field in {"genre_ids", "star_ids", "director_ids"}:
            if value is None:
                continue
            if field == "genre_ids":
                movie.genres = db.query(models.Genre).filter(models.Genre.id.in_(value)).all()
            elif field == "star_ids":
                movie.stars = db.query(models.Star).filter(models.Star.id.in_(value)).all()
            elif field == "director_ids":
                movie.directors = db.query(models.Director).filter(models.Director.id.in_(value)).all()
        else:
            setattr(movie, field, value)
    db.commit()
    db.refresh(movie)
    return movie


def delete_movie(db: Session, movie: models.Movie) -> None:
    db.delete(movie)
    db.commit()
