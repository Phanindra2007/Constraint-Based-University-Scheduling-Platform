from app.routers._crud import crud_router
from app.schemas.batches import BatchCreate, BatchResponse, BatchUpdate

router = crud_router(
    "batches",
    "batches",
    "Batches",
    ("id", "department_id", "name", "student_count"),
    BatchCreate,
    BatchUpdate,
    BatchResponse,
)
