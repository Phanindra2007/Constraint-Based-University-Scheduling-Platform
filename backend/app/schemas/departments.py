from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)


class DepartmentUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
