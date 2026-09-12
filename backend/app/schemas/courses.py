from typing import Literal

from pydantic import BaseModel, Field

RoomType = Literal["CLASSROOM", "LAB", "AUDITORIUM"]


class CourseCreate(BaseModel):
    department_id: int = Field(gt=0)
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    duration_minutes: int = Field(gt=0)
    sessions_per_week: int = Field(gt=0)
    required_room_type: RoomType
    min_capacity: int | None = Field(default=None, gt=0)


class CourseUpdate(BaseModel):
    department_id: int | None = Field(default=None, gt=0)
    code: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    duration_minutes: int | None = Field(default=None, gt=0)
    sessions_per_week: int | None = Field(default=None, gt=0)
    required_room_type: RoomType | None = None
    min_capacity: int | None = Field(default=None, gt=0)


class CourseResponse(CourseCreate):
    id: int
