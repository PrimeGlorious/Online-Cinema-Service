from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class StarBaseSchema(BaseModel):
    name: str


class StarCreateSchema(StarBaseSchema):
    pass


class StarUpdateSchema(StarBaseSchema):
    pass


class StarListItemSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class StarDetailSchema(StarListItemSchema):
    pass


class StarListResponseSchema(BaseModel):
    stars: List[StarListItemSchema]
    total_items: int
    total_pages: int
    prev_page: Optional[str]
    next_page: Optional[str]
