from app.routers._crud import crud_router
from app.schemas.faculty_availability import (
    FacultyAvailabilityCreate,
    FacultyAvailabilityResponse,
    FacultyAvailabilityUpdate,
)

router = crud_router(
    "faculty_availability",
    "faculty_availability",
    "Faculty Availability",
    ("id", "faculty_id", "semester_id", "day_of_week", "start_time", "end_time"),
    FacultyAvailabilityCreate,
    FacultyAvailabilityUpdate,
    FacultyAvailabilityResponse,
)
