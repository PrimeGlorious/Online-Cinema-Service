from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
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
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[float] = None
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None


class MovieRead(MovieBase):
    id: int
    uuid: UUID
    genres: List[GenreRead] = []
    stars: List[StarRead] = []
    directors: List[DirectorRead] = []
    certification: CertificationRead

    class Config:
        orm_mode = True


class Movie(MovieBase):
    id: int
    uuid: UUID

    class Config:
        orm_mode = True


class MovieLikeBase(BaseModel):
    movie_id: int
    like: bool


class MovieLikeCreate(MovieLikeBase):
    pass


class MovieCommentBase(BaseModel):
    movie_id: int
    text: str
    parent_comment_id: Optional[int] = None


class MovieCommentCreate(MovieCommentBase):
    pass


class MovieComment(MovieCommentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class MovieRatingBase(BaseModel):
    movie_id: int
    score: int = Field(..., ge=1, le=10)


class MovieRatingCreate(MovieRatingBase):
    pass


class MovieFavoriteBase(BaseModel):
    movie_id: int


class MovieFavoriteCreate(MovieFavoriteBase):
    pass


class NotificationType(str, Enum):
    reply = "reply"
    like = "like"
    mention = "mention"


class CommentNotificationBase(BaseModel):
    comment_id: int
    type: NotificationType


class CommentNotification(CommentNotificationBase):
    id: int
    user_id: int
    is_read: bool

    class Config:
        orm_mode = True
