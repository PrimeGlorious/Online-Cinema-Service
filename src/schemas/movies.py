from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict
)
from datetime import date
from typing import (
    List,
    Optional,
    Literal
)
from decimal import Decimal
from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    DATE = "date"
    SCORE = "score"
    PRICE = "price"
    VOTES = "votes"


class MovieFilterSchema(BaseModel):
    date_from: Optional[date] = Field(None, description="Filter movies released from this date")
    date_to: Optional[date] = Field(None, description="Filter movies released until this date")
    score_from: Optional[float] = Field(None, ge=0, le=10, description="Filter movies with score from")
    score_to: Optional[float] = Field(None, ge=0, le=10, description="Filter movies with score to")
    price_from: Optional[Decimal] = Field(None, ge=0, description="Filter movies with price from")
    price_to: Optional[Decimal] = Field(None, ge=0, description="Filter movies with price to")
    genre: Optional[str] = Field(None, description="Filter movies by genre")
    certification: Optional[str] = Field(None, description="Filter movies by certification")
    director: Optional[str] = Field(None, description="Filter movies by director")
    star: Optional[str] = Field(None, description="Filter movies by star")
    search: Optional[str] = Field(None, description="Search in movie title, description, director, or star names")
    sort_by: Optional[SortField] = Field(None, description="Field to sort by")
    sort_order: Optional[SortOrder] = Field(None, description="Sort order (asc/desc)")

    @field_validator("date_to")
    def validate_date_to(cls, v, values):
        if v is not None and "date_from" in values and values["date_from"] is not None:
            if v < values["date_from"]:
                raise ValueError("date_to must be greater than or equal to date_from")
        return v

    @field_validator("score_to")
    def validate_score_to(cls, v, values):
        if v is not None and "score_from" in values and values["score_from"] is not None:
            if v < values["score_from"]:
                raise ValueError("score_to must be greater than or equal to score_from")
        return v

    @field_validator("price_to")
    def validate_price_to(cls, v, values):
        if v is not None and "price_from" in values and values["price_from"] is not None:
            if v < values["price_from"]:
                raise ValueError("price_to must be greater than or equal to price_from")
        return v


class BaseEntitySchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    id: int
    uuid: str
    name: str = Field(..., min_length=1, max_length=255)
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: Literal["Released", "Post Production", "In Production"]

    certification: BaseEntitySchema
    genres: List[BaseEntitySchema]
    directors: List[BaseEntitySchema]
    stars: List[BaseEntitySchema]

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


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieUpdateSchema(MovieBaseSchema):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    certification_id: Optional[int] = None
    genres: Optional[List[int]] = None
    directors: Optional[List[int]] = None
    stars: Optional[List[int]] = None


class MovieResponseSchema(MovieBaseSchema):
    pass


class CreateUpdateBaseSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class GenreCreateSchema(CreateUpdateBaseSchema):
    pass


class GenreUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class StarCreateSchema(CreateUpdateBaseSchema):
    pass


class StarUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class DirectorCreateSchema(CreateUpdateBaseSchema):
    pass


class DirectorUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class CertificationCreateSchema(CreateUpdateBaseSchema):
    pass


class CertificationUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

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
