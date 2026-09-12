from app.routers._crud import crud_router
from app.schemas.departments import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

router = crud_router(
    table="departments",
    resource="departments",
    tag="Departments",
    columns=("id", "code", "name"),
    create_model=DepartmentCreate,
    update_model=DepartmentUpdate,
    response_model=DepartmentResponse,
)
