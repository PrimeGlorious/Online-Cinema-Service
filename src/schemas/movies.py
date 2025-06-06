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
from pydantic import condecimal
from schemas.examples.movies import (
    country_schema_example,
    language_schema_example,
    genre_schema_example,
    actor_schema_example,
    movie_item_schema_example,
    movie_list_response_schema_example,
    movie_create_schema_example,
    movie_detail_schema_example,
    movie_update_schema_example,
    star_schema_example
)


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
    price: condecimal(max_digits=10, decimal_places=2)
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


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                language_schema_example
            ]
        }
    }


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                country_schema_example
            ]
        }
    }


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                genre_schema_example
            ]
        }
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                star_schema_example
            ]
        }
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {"id": 1, "name": "Christopher Nolan"}
            ]
        }
    }


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    certification_id: Optional[int] = None
    genres: Optional[List[int]] = None
    directors: Optional[List[int]] = None
    stars: Optional[List[int]] = None


class MovieDetailSchema(MovieBaseSchema):
    id: int
    country: CountrySchema
    genres: List[GenreSchema]
    stars: List[StarSchema]
    languages: List[LanguageSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_detail_schema_example
            ]
        }
    }


class MovieResponseSchema(MovieBaseSchema):
    pass


class CreateUpdateBaseSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class GenreCreateSchema(CreateUpdateBaseSchema):
    pass


class GenreUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class GenreDeleteSchema(GenreSchema):
    pass


class GenreDetailSchema(GenreSchema):
    id: int
    movie_count: Optional[int] = Field(None, example=12)

    model_config = ConfigDict(from_attributes=True)


class GenreResponseSchema(GenreSchema):
    pass


class StarCreateSchema(CreateUpdateBaseSchema):
    pass


class StarUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class StarDeleteSchema(StarSchema):
    pass


class StarDetailSchema(StarSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DirectorCreateSchema(CreateUpdateBaseSchema):
    pass


class DirectorUpdateSchema(CreateUpdateBaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class DirectorDeleteSchema(DirectorSchema):
    pass


class DirectorDetailSchema(DirectorSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


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
