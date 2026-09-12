from datetime import date

from pydantic import BaseModel, Field, model_validator


class SemesterFields(BaseModel):
    name: str = Field(min_length=1)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class SemesterCreate(SemesterFields):
    pass


class SemesterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise ValueError("start_date must be before end_date")
        return self


class SemesterResponse(SemesterFields):
    id: int
