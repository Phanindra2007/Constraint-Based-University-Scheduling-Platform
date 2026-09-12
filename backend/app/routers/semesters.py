from app.routers._crud import crud_router
from app.schemas.semesters import SemesterCreate, SemesterResponse, SemesterUpdate

router = crud_router(
    "semesters",
    "semesters",
    "Semesters",
    ("id", "name", "start_date", "end_date"),
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse,
)
