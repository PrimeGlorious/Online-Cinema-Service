from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, Text, DECIMAL
from sqlalchemy.orm import relationship, declarative_base
import uuid as uuid_lib


Base = declarative_base()


movie_genres = Table(
    'movie_genres', Base.metadata,
    Column('movie_id', ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', ForeignKey('genres.id'), primary_key=True)
)


movie_stars = Table(
    'movie_stars', Base.metadata,
    Column('movie_id', ForeignKey('movies.id'), primary_key=True),
    Column('star_id', ForeignKey('stars.id'), primary_key=True)
)

movie_directors = Table(
    'movie_directors', Base.metadata,
    Column('movie_id', ForeignKey('movies.id'), primary_key=True),
    Column('director_id', ForeignKey('directors.id'), primary_key=True)
)


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Star(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Director(Base):
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, default=lambda: str(uuid_lib.uuid4()), unique=True, nullable=False)
    name = Column(String(250), nullable=False)
    year = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    imdb = Column(Float, nullable=False)
    votes = Column(Integer, nullable=False)
    meta_score = Column(Float)
    gross = Column(Float)
    description = Column(Text, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    certification_id = Column(Integer, ForeignKey("certifications.id"), nullable=False)

    certification = relationship("Certification", backref="movies")
    genres = relationship("Genre", secondary=movie_genres, backref="movies")
    stars = relationship("Star", secondary=movie_stars, backref="movies")
    directors = relationship("Director", secondary=movie_directors, backref="movies")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
