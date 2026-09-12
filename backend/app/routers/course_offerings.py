from app.routers._crud import crud_router
from app.schemas.course_offerings import (
    CourseOfferingCreate,
    CourseOfferingResponse,
    CourseOfferingUpdate,
)

router = crud_router(
    "course_offerings",
    "course_offerings",
    "Course Offerings",
    ("id", "course_id", "faculty_id", "batch_id", "semester_id"),
    CourseOfferingCreate,
    CourseOfferingUpdate,
    CourseOfferingResponse,
)
