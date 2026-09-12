from app.routers._crud import crud_router
from app.schemas.room_availability import (
    RoomAvailabilityCreate,
    RoomAvailabilityResponse,
    RoomAvailabilityUpdate,
)

router = crud_router(
    "room_availability",
    "room_availability",
    "Room Availability",
    ("id", "room_id", "semester_id", "day_of_week", "start_time", "end_time"),
    RoomAvailabilityCreate,
    RoomAvailabilityUpdate,
    RoomAvailabilityResponse,
)
