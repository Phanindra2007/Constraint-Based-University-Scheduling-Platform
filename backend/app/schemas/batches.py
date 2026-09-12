from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    department_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    student_count: int = Field(gt=0)


class BatchUpdate(BaseModel):
    department_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1)
    student_count: int | None = Field(default=None, gt=0)


class BatchResponse(BatchCreate):
    id: int
