from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, Table, DECIMAL, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base  # Імпорт базового класу з database.py

# Ассоціативні таблиці many-to-many

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

# Моделі

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
