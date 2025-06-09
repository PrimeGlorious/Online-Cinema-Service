from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class GenreCreateSchema(BaseModel):
    name: str


class GenreUpdateSchema(BaseModel):
    name: Optional[str]


class GenreListItemSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreDetailSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreListResponseSchema(BaseModel):
    genres: List[GenreListItemSchema]
    total: int
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
