from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


class CertificationBase(BaseModel):
    name: str


class CertificationCreate(CertificationBase):
    pass


class CertificationRead(CertificationBase):
    id: int

    class Config:
        orm_mode = True


class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreRead(GenreBase):
    id: int

    class Config:
        orm_mode = True


class StarBase(BaseModel):
    name: str


class StarCreate(StarBase):
    pass


class StarRead(StarBase):
    id: int

    class Config:
        orm_mode = True


class DirectorBase(BaseModel):
    name: str


class DirectorCreate(DirectorBase):
    pass


class DirectorRead(DirectorBase):
    id: int

    class Config:
        orm_mode = True


class MovieBase(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal
    certification_id: int
    genre_ids: List[int]
    star_ids: List[int]
    director_ids: List[int]


class MovieCreate(MovieBase):
    pass


class MovieUpdate(MovieBase):
    pass


class MovieRead(BaseModel):
    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: str
    price: Decimal
    certification: CertificationRead
    genres: List[GenreRead]
    stars: List[StarRead]
    directors: List[DirectorRead]

    class Config:
        orm_mode = True
