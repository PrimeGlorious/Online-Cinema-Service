from pydantic import (
    BaseModel,
    field_validator
)
from datetime import datetime


class MovieCommentCreateSchema(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment content cannot be empty.")
        if len(v) > 500:
            raise ValueError("Comment content must be at most 500 characters.")
        return v


class MovieCommentResponseSchema(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    movie_id: int

    model_config = {
        "from_attributes": True
    }
