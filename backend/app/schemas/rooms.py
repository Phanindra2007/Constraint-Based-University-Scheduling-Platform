from typing import Literal

from pydantic import BaseModel, Field

RoomType = Literal["CLASSROOM", "LAB", "AUDITORIUM"]


class RoomCreate(BaseModel):
    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    room_type: RoomType


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    capacity: int | None = Field(default=None, gt=0)
    room_type: RoomType | None = None


class RoomResponse(RoomCreate):
    id: int
