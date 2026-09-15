from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock
from typing import Protocol
from uuid import uuid4


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class TimetableGenerationJob:
    """In-memory state for one timetable-generation request."""

    job_id: str
    semester_id: int
    status: JobStatus
    timetable_id: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class TimetableGenerationJobStore(Protocol):
    """Storage contract that can later be backed by a persistent service."""

    def create_job(self, semester_id: int) -> TimetableGenerationJob: ...

    def get_job(self, job_id: str) -> TimetableGenerationJob | None: ...

    def mark_running(self, job_id: str) -> TimetableGenerationJob: ...

    def mark_completed(
        self, job_id: str, timetable_id: int
    ) -> TimetableGenerationJob: ...

    def mark_failed(
        self, job_id: str, error_message: str
    ) -> TimetableGenerationJob: ...


class InMemoryTimetableGenerationJobStore:
    """Thread-safe in-memory implementation of the job store contract."""

    def __init__(self) -> None:
        self._jobs: dict[str, TimetableGenerationJob] = {}
        self._lock = Lock()

    def create_job(self, semester_id: int) -> TimetableGenerationJob:
        job = TimetableGenerationJob(
            job_id=str(uuid4()),
            semester_id=semester_id,
            status=JobStatus.PENDING,
            timetable_id=None,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> TimetableGenerationJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> TimetableGenerationJob:
        with self._lock:
            job = self._require_job(job_id)
            job.status = JobStatus.RUNNING
            return job

    def mark_completed(
        self,
        job_id: str,
        timetable_id: int,
    ) -> TimetableGenerationJob:
        with self._lock:
            job = self._require_job(job_id)
            job.status = JobStatus.COMPLETED
            job.timetable_id = timetable_id
            job.error_message = None
            job.completed_at = datetime.now(timezone.utc)
            return job

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> TimetableGenerationJob:
        with self._lock:
            job = self._require_job(job_id)
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.now(timezone.utc)
            return job

    def _require_job(self, job_id: str) -> TimetableGenerationJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Unknown timetable-generation job_id: {job_id}")
        return job


job_store: TimetableGenerationJobStore = InMemoryTimetableGenerationJobStore()
