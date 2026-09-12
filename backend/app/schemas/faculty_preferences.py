from pydantic import Field

from app.schemas._time_windows import TimeWindowCreate, TimeWindowUpdate


class FacultyPreferenceCreate(TimeWindowCreate):
    faculty_id: int = Field(gt=0)
    semester_id: int = Field(gt=0)
    preference_score: int


class FacultyPreferenceUpdate(TimeWindowUpdate):
    faculty_id: int | None = Field(default=None, gt=0)
    semester_id: int | None = Field(default=None, gt=0)
    preference_score: int | None = None


class FacultyPreferenceResponse(FacultyPreferenceCreate):
    id: int
