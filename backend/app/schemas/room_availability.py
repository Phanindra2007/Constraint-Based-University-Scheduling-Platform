from pydantic import Field

from app.schemas._time_windows import TimeWindowCreate, TimeWindowUpdate


class RoomAvailabilityCreate(TimeWindowCreate):
    room_id: int = Field(gt=0)
    semester_id: int = Field(gt=0)


class RoomAvailabilityUpdate(TimeWindowUpdate):
    room_id: int | None = Field(default=None, gt=0)
    semester_id: int | None = Field(default=None, gt=0)


class RoomAvailabilityResponse(RoomAvailabilityCreate):
    id: int
