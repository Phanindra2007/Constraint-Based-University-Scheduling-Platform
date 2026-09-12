from app.routers._crud import crud_router
from app.schemas.faculty import FacultyCreate, FacultyResponse, FacultyUpdate

router = crud_router(
    "faculty",
    "faculty",
    "Faculty",
    ("id", "department_id", "name", "email"),
    FacultyCreate,
    FacultyUpdate,
    FacultyResponse,
)
