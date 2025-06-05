from sqlalchemy.orm import Session
from . import models, schemas


def create_certification(db: Session, certification: schemas.CertificationCreate):
    db_cert = models.Certification(**certification.dict())
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert


def create_genre(db: Session, genre: schemas.GenreCreate):
    db_genre = models.Genre(**genre.dict())
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre


def create_star(db: Session, star: schemas.StarCreate):
    db_star = models.Star(**star.dict())
    db.add(db_star)
    db.commit()
    db.refresh(db_star)
    return db_star


def create_director(db: Session, director: schemas.DirectorCreate):
    db_director = models.Director(**director.dict())
    db.add(db_director)
    db.commit()
    db.refresh(db_director)
    return db_director


def create_movie(db: Session, movie: schemas.MovieCreate):
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

    db_movie.genres = db.query(models.Genre).filter(models.Genre.id.in_(movie.genre_ids)).all()
    db_movie.stars = db.query(models.Star).filter(models.Star.id.in_(movie.star_ids)).all()
    db_movie.directors = db.query(models.Director).filter(models.Director.id.in_(movie.director_ids)).all()

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


def get_movie(db: Session, movie_id: int):
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()


def get_movies(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Movie).offset(skip).limit(limit).all()


def update_movie(db: Session, movie_id: int, movie_data: schemas.MovieUpdate):
    movie = get_movie(db, movie_id)
    if not movie:
        return None

    for field, value in movie_data.dict().items():
        if field.endswith('_ids'):
            continue
        setattr(movie, field, value)

    movie.genres = db.query(models.Genre).filter(models.Genre.id.in_(movie_data.genre_ids)).all()
    movie.stars = db.query(models.Star).filter(models.Star.id.in_(movie_data.star_ids)).all()
    movie.directors = db.query(models.Director).filter(models.Director.id.in_(movie_data.director_ids)).all()

    db.commit()
    db.refresh(movie)
    return movie


def delete_movie(db: Session, movie_id: int):
    movie = get_movie(db, movie_id)
    if movie:
        db.delete(movie)
        db.commit()
        return True
    return False
