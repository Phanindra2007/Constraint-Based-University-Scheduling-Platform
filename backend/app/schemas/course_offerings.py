from pydantic import BaseModel, Field


class CourseOfferingCreate(BaseModel):
    course_id: int = Field(gt=0)
    faculty_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)
    semester_id: int = Field(gt=0)


class CourseOfferingUpdate(BaseModel):
    course_id: int | None = Field(default=None, gt=0)
    faculty_id: int | None = Field(default=None, gt=0)
    batch_id: int | None = Field(default=None, gt=0)
    semester_id: int | None = Field(default=None, gt=0)


class CourseOfferingResponse(CourseOfferingCreate):
    id: int
