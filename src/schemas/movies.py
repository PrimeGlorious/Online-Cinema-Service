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
