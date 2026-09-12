from app.routers._crud import crud_router
from app.schemas.rooms import RoomCreate, RoomResponse, RoomUpdate

router = crud_router(
    "rooms",
    "rooms",
    "Rooms",
    ("id", "name", "capacity", "room_type"),
    RoomCreate,
    RoomUpdate,
    RoomResponse,
)
