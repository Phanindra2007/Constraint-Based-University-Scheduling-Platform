from pydantic import BaseModel, Field


class FacultyCreate(BaseModel):
    department_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)


class FacultyUpdate(BaseModel):
    department_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)


class FacultyResponse(FacultyCreate):
    id: int
