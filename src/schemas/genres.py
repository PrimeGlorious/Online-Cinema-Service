from pydantic import BaseModel
from typing import Optional, List


class GenreCreateSchema(BaseModel):
    name: str


class GenreUpdateSchema(BaseModel):
    name: Optional[str]


class GenreListItemSchema(BaseModel):
    id: int
    name: str


class GenreDetailSchema(BaseModel):
    id: int
    name: str


class GenreListResponseSchema(BaseModel):
    genres: List[GenreListItemSchema]
    total: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
