from datetime import time

from pydantic import BaseModel, Field, model_validator


class TimeWindowCreate(BaseModel):
    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class TimeWindowUpdate(BaseModel):
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.start_time >= self.end_time
        ):
            raise ValueError("start_time must be before end_time")
        return self
