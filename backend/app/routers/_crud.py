from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, HTTPException
from psycopg import IntegrityError
from pydantic import BaseModel

from app.database.queries import (
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
)


def crud_router(
    table: str,
    resource: str,
    tag: str,
    columns: Sequence[str],
    create_model: type[BaseModel],
    update_model: type[BaseModel],
    response_model: type[BaseModel],
) -> APIRouter:
    router = APIRouter(prefix=f"/api/{resource}", tags=[tag])
    item_name = {
        "faculty": "Faculty member",
        "course_offerings": "Course offering",
        "faculty_availability": "Faculty availability",
        "room_availability": "Room availability",
        "faculty_preferences": "Faculty preference",
    }.get(resource, resource.rstrip("s").replace("_", " ").title())

    def database_error() -> HTTPException:
        return HTTPException(
            status_code=409, detail=f"Unable to modify {item_name.lower()}"
        )

    @router.get("", response_model=list[response_model])
    def list_items() -> list[dict[str, Any]]:
        return list_records(table, columns)

    @router.get("/{record_id}", response_model=response_model)
    def get_item(record_id: int) -> dict[str, Any]:
        record = get_record(table, columns, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"{item_name} not found")
        return record

    @router.post("", response_model=response_model, status_code=201)
    def create_item(item: create_model) -> dict[str, Any]:  # type: ignore[valid-type]
        try:
            return create_record(table, columns, item.model_dump())
        except IntegrityError as exc:
            raise database_error() from exc

    @router.patch("/{record_id}", response_model=response_model)
    def update_item(record_id: int, item: update_model) -> dict[str, Any]:  # type: ignore[valid-type]
        values = item.model_dump(exclude_unset=True)
        if not values:
            raise HTTPException(
                status_code=422, detail="At least one field is required"
            )
        try:
            record = update_record(table, columns, record_id, values)
        except IntegrityError as exc:
            raise database_error() from exc
        if record is None:
            raise HTTPException(status_code=404, detail=f"{item_name} not found")
        return record

    @router.delete("/{record_id}", status_code=204)
    def delete_item(record_id: int) -> None:
        try:
            deleted = delete_record(table, columns, record_id)
        except IntegrityError as exc:
            raise database_error() from exc
        if not deleted:
            raise HTTPException(status_code=404, detail=f"{item_name} not found")

    return router
