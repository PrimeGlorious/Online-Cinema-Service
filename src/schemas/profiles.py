from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum


class GenderEnum(str, Enum):
    MAN = "man"
    WOMAN = "woman"


class UserProfileBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class UserProfileOut(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: GenderEnum
    info: Optional[str] = None

    class Config:
        orm_mode = True
