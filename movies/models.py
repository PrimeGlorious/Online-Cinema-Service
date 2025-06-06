from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, Table,
    DECIMAL, Boolean, UniqueConstraint, DateTime, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base  # Імпорт базового класу з database.py


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("star_id", Integer, ForeignKey("stars.id"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("director_id", Integer, ForeignKey("directors.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    movies = relationship(
        "Movie",
        secondary=movie_genres,
        back_populates="genres"
    )


class Star(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    movies = relationship(
        "Movie",
        secondary=movie_stars,
        back_populates="stars"
    )


class Director(Base):
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    movies = relationship(
        "Movie",
        secondary=movie_directors,
        back_populates="directors"
    )


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    movies = relationship("Movie", back_populates="certification")


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uix_name_year_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)  # Тривалість у хвилинах
    imdb = Column(Float, nullable=False)
    votes = Column(Integer, nullable=False)
    meta_score = Column(Float, nullable=True)
    gross = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)
    certification_id = Column(Integer, ForeignKey("certifications.id"), nullable=False)

    certification = relationship("Certification", back_populates="movies")
    genres = relationship("Genre", secondary=movie_genres, back_populates="movies")
    stars = relationship("Star", secondary=movie_stars, back_populates="movies")
    directors = relationship("Director", secondary=movie_directors, back_populates="movies")

    likes = relationship("MovieLike", back_populates="movie", cascade="all, delete-orphan")
    comments = relationship("MovieComment", back_populates="movie", cascade="all, delete-orphan")
    ratings = relationship("MovieRating", back_populates="movie", cascade="all, delete-orphan")
    favorites = relationship("MovieFavorite", back_populates="movie", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)

    likes = relationship("MovieLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("MovieComment", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("MovieRating", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("MovieFavorite", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("CommentNotification", back_populates="user", cascade="all, delete-orphan")


class MovieLike(Base):
    __tablename__ = "movie_likes"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    like = Column(Boolean, nullable=False)  # True - лайк, False - дизлайк

    movie = relationship("Movie", back_populates="likes")
    user = relationship("User", back_populates="likes")

    __table_args__ = (
        UniqueConstraint('movie_id', 'user_id', name='uix_movie_user_like'),
    )


class MovieComment(Base):
    __tablename__ = "movie_comments"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parent_comment_id = Column(Integer, ForeignKey("movie_comments.id"), nullable=True)  # для відповідей

    movie = relationship("Movie", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("MovieComment", backref="parent", remote_side=[id], cascade="all, delete-orphan")
    notifications = relationship("CommentNotification", back_populates="comment", cascade="all, delete-orphan")


class MovieRating(Base):
    __tablename__ = "movie_ratings"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)  # 1-10

    movie = relationship("Movie", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint('movie_id', 'user_id', name='uix_movie_user_rating'),
    )


class MovieFavorite(Base):
    __tablename__ = "movie_favorites"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    movie = relationship("Movie", back_populates="favorites")
    user = relationship("User", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint('movie_id', 'user_id', name='uix_movie_user_favorite'),
    )


class CommentNotification(Base):
    __tablename__ = "comment_notifications"
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("movie_comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # користувач, який отримує сповіщення
    type = Column(String, nullable=False)  # наприклад, 'reply' або 'like'
    is_read = Column(Boolean, default=False)

    comment = relationship("MovieComment", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
