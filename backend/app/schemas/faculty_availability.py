from pydantic import Field

from app.schemas._time_windows import TimeWindowCreate, TimeWindowUpdate


class FacultyAvailabilityCreate(TimeWindowCreate):
    faculty_id: int = Field(gt=0)
    semester_id: int = Field(gt=0)


class FacultyAvailabilityUpdate(TimeWindowUpdate):
    faculty_id: int | None = Field(default=None, gt=0)
    semester_id: int | None = Field(default=None, gt=0)


class FacultyAvailabilityResponse(FacultyAvailabilityCreate):
    id: int
