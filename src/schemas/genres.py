from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    NAME = "name"
    MOVIE_COUNT = "movie_count"


class GenreFilterSchema(BaseModel):
    sort_by: Optional[SortField] = Field(None, description="Field to sort by")
    sort_order: Optional[SortOrder] = Field(None, description="Sort order (asc/desc)")


class GenreCreateSchema(BaseModel):
    name: str


class GenreUpdateSchema(BaseModel):
    name: Optional[str]


class GenreListItemSchema(BaseModel):
    id: int
    name: str
    movie_count: int

    model_config = ConfigDict(from_attributes=True)


class GenreDetailSchema(BaseModel):
    id: int
    name: str
    movie_count: int

    model_config = ConfigDict(from_attributes=True)


class GenreListResponseSchema(BaseModel):
    genres: List[GenreListItemSchema]
    total: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
