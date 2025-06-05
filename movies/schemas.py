from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# --- Genre ---

class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreRead(GenreBase):
    id: int

    class Config:
        orm_mode = True


# --- Star ---

class StarBase(BaseModel):
    name: str


class StarCreate(StarBase):
    pass


class StarRead(StarBase):
    id: int

    class Config:
        orm_mode = True


# --- Director ---

class DirectorBase(BaseModel):
    name: str


class DirectorCreate(DirectorBase):
    pass


class DirectorRead(DirectorBase):
    id: int

    class Config:
        orm_mode = True


# --- Certification ---

class CertificationBase(BaseModel):
    name: str


class CertificationCreate(CertificationBase):
    pass


class CertificationRead(CertificationBase):
    id: int

    class Config:
        orm_mode = True


# --- Movie ---

class MovieBase(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Optional[float] = None
    certification_id: int


class MovieCreate(MovieBase):
    genre_ids: List[int] = Field(default_factory=list)
    star_ids: List[int] = Field(default_factory=list)
    director_ids: List[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    name: Optional[str]
    year: Optional[int]
    time: Optional[int]
    imdb: Optional[float]
    votes: Optional[int]
    meta_score: Optional[float]
    gross: Optional[float]
    description: Optional[str]
    price: Optional[float]
    certification_id: Optional[int]
    genre_ids: Optional[List[int]]
    star_ids: Optional[List[int]]
    director_ids: Optional[List[int]]


class MovieRead(MovieBase):
    id: int
    uuid: UUID
    genres: List[GenreRead] = []
    stars: List[StarRead] = []
    directors: List[DirectorRead] = []
    certification: CertificationRead

    class Config:
        orm_mode = True
