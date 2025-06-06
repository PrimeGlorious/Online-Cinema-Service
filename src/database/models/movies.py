from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    DECIMAL,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column
)
from enum import Enum
from typing import (
    List,
    Optional
)

from database import Base
from .carts import CartItemModel


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary="movie_genres",
        back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary="movie_stars",
        back_populates="stars"
    )

    def __repr__(self):
        return f"<Star(name='{self.name}')>"


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary="movie_directors",
        back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(name='{self.name}')>"


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        back_populates="certification"
    )

    def __repr__(self):
        return f"<Certification(name='{self.name}')>"


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    cart: Mapped[Optional["CartItemModel"]] = relationship(
        "CartItemModel", back_populates="movie", uselist=False
    )

    certification: Mapped["CertificationModel"] = relationship("CertificationModel", back_populates="movies")
    genres: Mapped[List["GenreModel"]] = relationship(
        "GenreModel",
        secondary="movie_genres",
        back_populates="movies"
    )
    directors: Mapped[List["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary="movie_directors",
        back_populates="movies"
    )
    stars: Mapped[List["StarModel"]] = relationship(
        "StarModel",
        secondary="movie_stars",
        back_populates="movies"
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, time={self.time})>"


class MovieGenreModel(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)


class MovieDirectorModel(Base):
    __tablename__ = "movie_directors"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    director_id: Mapped[int] = mapped_column(ForeignKey("directors.id"), primary_key=True)


class MovieStarModel(Base):
    __tablename__ = "movie_stars"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    star_id: Mapped[int] = mapped_column(ForeignKey("stars.id"), primary_key=True)
