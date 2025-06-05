from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, desc, asc
from . import models, schemas
from models import Movie, MovieLike, MovieComment, MovieRating, MovieFavorite, Director, Star
from schemas import (
    GenreCreate, StarCreate, DirectorCreate, CertificationCreate,
    MovieCreate, MovieUpdate, MovieLikeCreate, MovieCommentCreate,
    MovieRatingCreate, MovieFavoriteCreate,
)

# --- Genres ---

def get_genre(db: Session, genre_id: int) -> Optional[models.Genre]:
    return db.query(models.Genre).filter(models.Genre.id == genre_id).first()

def get_genres(db: Session, skip: int = 0, limit: int = 100) -> List[models.Genre]:
    return db.query(models.Genre).offset(skip).limit(limit).all()

def create_genre(db: Session, genre: GenreCreate) -> models.Genre:
    db_genre = models.Genre(name=genre.name)
    try:
        db.add(db_genre)
        db.commit()
        db.refresh(db_genre)
    except IntegrityError:
        db.rollback()
        raise
    return db_genre

# --- Stars ---

def get_star(db: Session, star_id: int) -> Optional[models.Star]:
    return db.query(models.Star).filter(models.Star.id == star_id).first()

def get_stars(db: Session, skip: int = 0, limit: int = 100) -> List[models.Star]:
    return db.query(models.Star).offset(skip).limit(limit).all()

def create_star(db: Session, star: StarCreate) -> models.Star:
    db_star = models.Star(name=star.name)
    try:
        db.add(db_star)
        db.commit()
        db.refresh(db_star)
    except IntegrityError:
        db.rollback()
        raise
    return db_star

# --- Directors ---

def get_director(db: Session, director_id: int) -> Optional[models.Director]:
    return db.query(models.Director).filter(models.Director.id == director_id).first()

def get_directors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Director]:
    return db.query(models.Director).offset(skip).limit(limit).all()

def create_director(db: Session, director: DirectorCreate) -> models.Director:
    db_director = models.Director(name=director.name)
    try:
        db.add(db_director)
        db.commit()
        db.refresh(db_director)
    except IntegrityError:
        db.rollback()
        raise
    return db_director

# --- Certifications ---

def get_certification(db: Session, certification_id: int) -> Optional[models.Certification]:
    return db.query(models.Certification).filter(models.Certification.id == certification_id).first()

def get_certifications(db: Session, skip: int = 0, limit: int = 100) -> List[models.Certification]:
    return db.query(models.Certification).offset(skip).limit(limit).all()

def create_certification(db: Session, certification: CertificationCreate) -> models.Certification:
    db_cert = models.Certification(name=certification.name)
    try:
        db.add(db_cert)
        db.commit()
        db.refresh(db_cert)
    except IntegrityError:
        db.rollback()
        raise
    return db_cert

# --- Movies ---

def get_movie(db: Session, movie_id: int) -> Optional[models.Movie]:
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()

def get_movie_by_uuid(db: Session, movie_uuid: str) -> Optional[models.Movie]:
    return db.query(models.Movie).filter(models.Movie.uuid == movie_uuid).first()

def get_movies(db: Session, skip: int = 0, limit: int = 100) -> List[models.Movie]:
    return db.query(models.Movie).offset(skip).limit(limit).all()

def create_movie(db: Session, movie: MovieCreate) -> models.Movie:
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
    # Add relations if provided
    if movie.genre_ids:
        db_movie.genres = db.query(models.Genre).filter(models.Genre.id.in_(movie.genre_ids)).all()
    if movie.star_ids:
        db_movie.stars = db.query(models.Star).filter(models.Star.id.in_(movie.star_ids)).all()
    if movie.director_ids:
        db_movie.directors = db.query(models.Director).filter(models.Director.id.in_(movie.director_ids)).all()

    try:
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
    except IntegrityError:
        db.rollback()
        raise
    return db_movie

def update_movie(db: Session, movie: models.Movie, movie_update: MovieUpdate) -> models.Movie:
    update_data = movie_update.dict(exclude_unset=True)
    for field, value in update_data.items():
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
    try:
        db.commit()
        db.refresh(movie)
    except IntegrityError:
        db.rollback()
        raise
    return movie

def delete_movie(db: Session, movie: models.Movie) -> None:
    try:
        db.delete(movie)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

# --- Likes ---

def create_movie_like(db: Session, user_id: int, like_data: MovieLikeCreate) -> MovieLike:
    existing = db.query(MovieLike).filter_by(movie_id=like_data.movie_id, user_id=user_id).first()
    if existing:
        existing.like = like_data.like
        try:
            db.commit()
            db.refresh(existing)
        except IntegrityError:
            db.rollback()
            raise
        return existing
    new_like = MovieLike(movie_id=like_data.movie_id, user_id=user_id, like=like_data.like)
    try:
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
    except IntegrityError:
        db.rollback()
        raise
    return new_like

# --- Comments ---

def create_movie_comment(db: Session, user_id: int, comment_data: MovieCommentCreate) -> MovieComment:
    comment = MovieComment(
        movie_id=comment_data.movie_id,
        user_id=user_id,
        text=comment_data.text,
        parent_comment_id=comment_data.parent_comment_id,
    )
    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)
    except IntegrityError:
        db.rollback()
        raise
    return comment

def get_movie_comments(db: Session, movie_id: int, skip: int = 0, limit: int = 100) -> List[MovieComment]:
    return db.query(MovieComment).filter_by(movie_id=movie_id).offset(skip).limit(limit).all()

# --- Ratings ---

def create_movie_rating(db: Session, user_id: int, rating_data: MovieRatingCreate) -> MovieRating:
    existing = db.query(MovieRating).filter_by(movie_id=rating_data.movie_id, user_id=user_id).first()
    if existing:
        existing.score = rating_data.score
        try:
            db.commit()
            db.refresh(existing)
        except IntegrityError:
            db.rollback()
            raise
        return existing
    new_rating = MovieRating(movie_id=rating_data.movie_id, user_id=user_id, score=rating_data.score)
    try:
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
    except IntegrityError:
        db.rollback()
        raise
    return new_rating

# --- Favorites ---

def add_movie_favorite(db: Session, user_id: int, fav_data: MovieFavoriteCreate) -> MovieFavorite:
    existing = db.query(MovieFavorite).filter_by(movie_id=fav_data.movie_id, user_id=user_id).first()
    if existing:
        return existing
    new_fav = MovieFavorite(movie_id=fav_data.movie_id, user_id=user_id)
    try:
        db.add(new_fav)
        db.commit()
        db.refresh(new_fav)
    except IntegrityError:
        db.rollback()
        raise
    return new_fav

def remove_movie_favorite(db: Session, user_id: int, movie_id: int) -> bool:
    fav = db.query(MovieFavorite).filter_by(movie_id=movie_id, user_id=user_id).first()
    if fav:
        try:
            db.delete(fav)
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            raise
    return False

# --- Search, Filter, Sort Movies ---

def search_filter_sort_movies(
    db: Session,
    search: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    imdb_from: Optional[float] = None,
    imdb_to: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_desc: bool = True,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[int, List[Movie]]:

    query = db.query(Movie)

    if search:
        search_like = f"%{search}%"
        # Для унікального приєднання використаємо аліаси, щоб не дублювати join-и
        query = query.join(Movie.directors, isouter=True).join(Movie.stars, isouter=True)
        query = query.filter(
            or_(
                Movie.name.ilike(search_like),
                Movie.description.ilike(search_like),
                Director.name.ilike(search_like),
                Star.name.ilike(search_like),
            )
        )

    if year_from is not None:
        query = query.filter(Movie.year >= year_from)
    if year_to is not None:
        query = query.filter(Movie.year <= year_to)
    if imdb_from is not None:
        query = query.filter(Movie.imdb >= imdb_from)
    if imdb_to is not None:
        query = query.filter(Movie.imdb <= imdb_to)

    if sort_by:
        col = getattr(Movie, sort_by, None)
        if col is not None:
            query = query.order_by(desc(col) if sort_desc else asc(col))

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items
