from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# --- Genre ---

class GenreBase(BaseModel):
    """Base schema for Genre with the name field."""
    name: str


class GenreCreate(GenreBase):
    """Schema for creating a Genre."""
    pass


class GenreUpdate(BaseModel):
    """Schema for updating a Genre."""
    name: Optional[str] = None


class GenreRead(GenreBase):
    """Schema for reading Genre, including the ID."""
    id: int

    class Config:
        orm_mode = True


# --- Star ---

class StarBase(BaseModel):
    """Base schema for Star (actor) with the name field."""
    name: str


class StarCreate(StarBase):
    """Schema for creating a Star."""
    pass


class StarUpdate(BaseModel):
    """Schema for updating a Star."""
    name: Optional[str] = None


class StarRead(StarBase):
    """Schema for reading Star, including the ID."""
    id: int

    class Config:
        orm_mode = True


# --- Director ---

class DirectorBase(BaseModel):
    """Base schema for Director with the name field."""
    name: str


class DirectorCreate(DirectorBase):
    """Schema for creating a Director."""
    pass


class DirectorUpdate(BaseModel):
    """Schema for updating a Director."""
    name: Optional[str] = None


class DirectorRead(DirectorBase):
    """Schema for reading Director, including the ID."""
    id: int

    class Config:
        orm_mode = True


# --- Certification ---

class CertificationBase(BaseModel):
    """Base schema for Certification with the name field."""
    name: str


class CertificationCreate(CertificationBase):
    """Schema for creating a Certification."""
    pass


class CertificationUpdate(BaseModel):
    """Schema for updating a Certification."""
    name: Optional[str] = None


class CertificationRead(CertificationBase):
    """Schema for reading Certification, including the ID."""
    id: int

    class Config:
        orm_mode = True


# --- Movie ---

class MovieBase(BaseModel):
    """Base schema for Movie with main movie attributes."""
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
    """Schema for creating a Movie including related entity IDs."""
    genre_ids: List[int] = Field(default_factory=list)
    star_ids: List[int] = Field(default_factory=list)
    director_ids: List[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    """Schema for updating a Movie with all fields optional."""
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
    """Schema for reading a Movie, including related nested objects."""
    id: int
    uuid: UUID
    genres: List[GenreRead] = Field(default_factory=list)
    stars: List[StarRead] = Field(default_factory=list)
    directors: List[DirectorRead] = Field(default_factory=list)
    certification: CertificationRead

    class Config:
        orm_mode = True


class Movie(MovieBase):
    """Movie schema including ID and UUID, used internally."""
    id: int
    uuid: UUID

    class Config:
        orm_mode = True


# --- Movie Like ---

class MovieLikeBase(BaseModel):
    """Base schema for liking or disliking a movie."""
    movie_id: int
    like: bool


class MovieLikeCreate(MovieLikeBase):
    """Schema for creating a like/dislike entry."""
    pass


# --- Movie Comment ---

class MovieCommentBase(BaseModel):
    """Base schema for a movie comment."""
    movie_id: int
    text: str
    parent_comment_id: Optional[int] = None


class MovieCommentCreate(MovieCommentBase):
    """Schema for creating a movie comment."""
    pass


class MovieComment(MovieCommentBase):
    """Schema for reading a movie comment with metadata."""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# --- Movie Rating ---

class MovieRatingBase(BaseModel):
    """Base schema for rating a movie."""
    movie_id: int
    score: int = Field(..., ge=1, le=10)


class MovieRatingCreate(MovieRatingBase):
    """Schema for creating a movie rating."""
    pass


# --- Movie Favorite ---

class MovieFavoriteBase(BaseModel):
    """Base schema for marking a movie as favorite."""
    movie_id: int


class MovieFavoriteCreate(MovieFavoriteBase):
    """Schema for creating a favorite entry."""
    pass


# --- Notifications ---

class NotificationType(str, Enum):
    """Enum of notification types."""
    reply = "reply"
    like = "like"
    mention = "mention"


class CommentNotificationBase(BaseModel):
    """Base schema for a comment notification."""
    comment_id: int
    type: NotificationType


class CommentNotification(CommentNotificationBase):
    """Schema for reading a comment notification."""
    id: int
    user_id: int
    is_read: bool

    class Config:
        orm_mode = True
