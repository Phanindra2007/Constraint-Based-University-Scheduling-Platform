from app.routers._crud import crud_router
from app.schemas.faculty_preferences import (
    FacultyPreferenceCreate,
    FacultyPreferenceResponse,
    FacultyPreferenceUpdate,
)

router = crud_router(
    "faculty_preferences",
    "faculty_preferences",
    "Faculty Preferences",
    (
        "id",
        "faculty_id",
        "semester_id",
        "day_of_week",
        "start_time",
        "end_time",
        "preference_score",
    ),
    FacultyPreferenceCreate,
    FacultyPreferenceUpdate,
    FacultyPreferenceResponse,
)
