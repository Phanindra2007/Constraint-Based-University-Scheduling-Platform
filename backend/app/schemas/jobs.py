from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.scheduler.jobs import JobStatus, TimetableGenerationJob


class TimetableGenerationJobResponse(BaseModel):
    """Public representation of a timetable-generation job."""

    model_config = ConfigDict(from_attributes=True)

    job_id: str
    semester_id: int
    status: JobStatus
    timetable_id: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_job(cls, job: TimetableGenerationJob) -> "TimetableGenerationJobResponse":
        return cls.model_validate(job)
