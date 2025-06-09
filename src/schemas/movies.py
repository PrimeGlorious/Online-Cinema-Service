from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict
)
from typing import (
    List,
    Optional,
)
from decimal import Decimal


class BaseEntitySchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal = Field(..., max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("year")
    def validate_year(cls, v):
        if v < 1900:
            raise ValueError("Year must be greater than or equal to 1900.")
        return v

    @field_validator("time")
    def validate_time(cls, v):
        if v <= 0:
            raise ValueError("Time must be positive.")
        return v


class MovieListItemSchema(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: Decimal
    votes: int
    meta_score: Decimal
    price: Decimal

    model_config = {
        "from_attributes": True,
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }


class MovieDetailResponseSchema(MovieBaseSchema):
    id: int
    uuid: UUID
    certification: BaseEntitySchema
    genres: List[BaseEntitySchema]
    directors: List[BaseEntitySchema]
    stars: List[BaseEntitySchema]


class MovieCreateSchema(MovieBaseSchema):
    certification: str
    genres: List[str]
    directors: List[str]
    stars: List[str]
