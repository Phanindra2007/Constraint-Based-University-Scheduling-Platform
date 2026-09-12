from app.routers._crud import crud_router
from app.schemas.courses import CourseCreate, CourseResponse, CourseUpdate

router = crud_router(
    "courses",
    "courses",
    "Courses",
    (
        "id",
        "department_id",
        "code",
        "name",
        "duration_minutes",
        "sessions_per_week",
        "required_room_type",
        "min_capacity",
    ),
    CourseCreate,
    CourseUpdate,
    CourseResponse,
)
