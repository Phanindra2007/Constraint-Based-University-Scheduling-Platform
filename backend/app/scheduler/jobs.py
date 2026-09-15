from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock
from typing import Protocol
from uuid import uuid4

from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from app.database.connection import get_connection


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InvalidJobTransitionError(ValueError):
    """Raised when a job status transition is not allowed."""


class ActiveGenerationJobExistsError(ValueError):
    """Raised when a semester already has an active generation job."""


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
            if any(
                existing.semester_id == semester_id
                and existing.status in (JobStatus.PENDING, JobStatus.RUNNING)
                for existing in self._jobs.values()
            ):
                raise ActiveGenerationJobExistsError(
                    f"An active timetable-generation job already exists for "
                    f"semester_id={semester_id}."
                )
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> TimetableGenerationJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> TimetableGenerationJob:
        with self._lock:
            job = self._require_job(job_id)
            self._require_status(job, JobStatus.PENDING, JobStatus.RUNNING)
            job.status = JobStatus.RUNNING
            return job

    def mark_completed(
        self,
        job_id: str,
        timetable_id: int,
    ) -> TimetableGenerationJob:
        with self._lock:
            job = self._require_job(job_id)
            self._require_status(job, JobStatus.RUNNING, JobStatus.COMPLETED)
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
            self._require_status(job, JobStatus.RUNNING, JobStatus.FAILED)
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.now(timezone.utc)
            return job

    def _require_job(self, job_id: str) -> TimetableGenerationJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Unknown timetable-generation job_id: {job_id}")
        return job

    def _require_status(
        self,
        job: TimetableGenerationJob,
        expected_status: JobStatus,
        target_status: JobStatus,
    ) -> None:
        if job.status != expected_status:
            raise InvalidJobTransitionError(
                f"Cannot transition job_id={job.job_id} from "
                f"{job.status} to {target_status}; expected "
                f"{expected_status}."
            )


class PostgresTimetableGenerationJobStore:
    """PostgreSQL-backed implementation of the timetable job store."""

    _TABLE = "timetable_generation_jobs"
    _COLUMNS = (
        "id, semester_id, status, timetable_id, error_message, "
        "created_at, completed_at"
    )

    def create_job(self, semester_id: int) -> TimetableGenerationJob:
        try:
            with get_connection() as connection:
                with connection.transaction():
                    with connection.cursor(row_factory=dict_row) as cursor:
                        cursor.execute(
                            """
                            INSERT INTO timetable_generation_jobs (semester_id, status)
                            VALUES (%s, %s)
                            RETURNING id, semester_id, status, timetable_id,
                                      error_message, created_at, completed_at
                            """,
                            (semester_id, JobStatus.PENDING.value),
                        )
                        row = cursor.fetchone()
                        if row is None:
                            raise RuntimeError("Job insert did not return a row")
                        return self._row_to_job(row)
        except UniqueViolation as error:
            if error.diag.constraint_name != (
                "uq_timetable_generation_jobs_active_semester"
            ):
                raise
            raise ActiveGenerationJobExistsError(
                f"An active timetable-generation job already exists for "
                f"semester_id={semester_id}."
            ) from error

    def get_job(self, job_id: str) -> TimetableGenerationJob | None:
        try:
            job_id_value = self._job_id_value(job_id)
        except KeyError:
            return None
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, semester_id, status, timetable_id,
                           error_message, created_at, completed_at
                    FROM timetable_generation_jobs
                    WHERE id = %s
                    """,
                    (job_id_value,),
                )
                row = cursor.fetchone()
                return None if row is None else self._row_to_job(row)

    def mark_running(self, job_id: str) -> TimetableGenerationJob:
        return self._transition(
            job_id,
            expected_status=JobStatus.PENDING,
            target_status=JobStatus.RUNNING,
            values=(JobStatus.RUNNING.value,),
        )

    def mark_completed(
        self,
        job_id: str,
        timetable_id: int,
    ) -> TimetableGenerationJob:
        return self._transition(
            job_id,
            expected_status=JobStatus.RUNNING,
            target_status=JobStatus.COMPLETED,
            values=(JobStatus.COMPLETED.value, timetable_id),
        )

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> TimetableGenerationJob:
        return self._transition(
            job_id,
            expected_status=JobStatus.RUNNING,
            target_status=JobStatus.FAILED,
            values=(JobStatus.FAILED.value, error_message),
        )

    def _transition(
        self,
        job_id: str,
        *,
        expected_status: JobStatus,
        target_status: JobStatus,
        values: tuple[object, ...],
    ) -> TimetableGenerationJob:
        job_id_value = self._job_id_value(job_id)
        with get_connection() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    if target_status is JobStatus.RUNNING:
                        query = """
                            UPDATE timetable_generation_jobs
                            SET status = %s, completed_at = NULL
                            WHERE id = %s AND status = %s
                            RETURNING id, semester_id, status, timetable_id,
                                      error_message, created_at, completed_at
                        """
                        query_values = (values[0], job_id_value, expected_status.value)
                    elif target_status is JobStatus.COMPLETED:
                        query = """
                            UPDATE timetable_generation_jobs
                            SET status = %s, timetable_id = %s,
                                error_message = NULL,
                                completed_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND status = %s
                            RETURNING id, semester_id, status, timetable_id,
                                      error_message, created_at, completed_at
                        """
                        query_values = (*values, job_id_value, expected_status.value)
                    else:
                        query = """
                            UPDATE timetable_generation_jobs
                            SET status = %s, timetable_id = NULL,
                                error_message = %s,
                                completed_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND status = %s
                            RETURNING id, semester_id, status, timetable_id,
                                      error_message, created_at, completed_at
                        """
                        query_values = (*values, job_id_value, expected_status.value)
                    cursor.execute(
                        query,
                        query_values,
                    )
                    row = cursor.fetchone()
                    if row is not None:
                        return self._row_to_job(row)

                    cursor.execute(
                        """
                        SELECT status
                        FROM timetable_generation_jobs
                        WHERE id = %s
                        """,
                        (job_id_value,),
                    )
                    current = cursor.fetchone()
                    if current is None:
                        raise KeyError(f"Unknown timetable-generation job_id: {job_id}")
                    raise InvalidJobTransitionError(
                        f"Cannot transition job_id={job_id} from "
                        f"{current['status']} to {target_status}; expected "
                        f"{expected_status}."
                    )

    @staticmethod
    def _job_id_value(job_id: str) -> int:
        try:
            return int(job_id)
        except (TypeError, ValueError) as error:
            raise KeyError(f"Unknown timetable-generation job_id: {job_id}") from error

    @staticmethod
    def _row_to_job(row: dict) -> TimetableGenerationJob:
        return TimetableGenerationJob(
            job_id=str(row["id"]),
            semester_id=row["semester_id"],
            status=JobStatus(row["status"]),
            timetable_id=row["timetable_id"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )


job_store: TimetableGenerationJobStore = PostgresTimetableGenerationJobStore()
