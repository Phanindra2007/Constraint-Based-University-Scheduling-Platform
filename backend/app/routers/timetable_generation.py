import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status

from app.scheduler.jobs import (
    ActiveGenerationJobExistsError,
    TimetableGenerationJob,
    TimetableGenerationJobStore,
    job_store,
)
from app.scheduler.service import generate_timetable
from app.schemas.jobs import TimetableGenerationJobResponse

router = APIRouter(prefix="/api", tags=["Timetable generation"])
logger = logging.getLogger(__name__)


def get_job_store() -> TimetableGenerationJobStore:
    """Return the production job store used by the API."""

    return job_store


def run_timetable_generation_job(
    job: TimetableGenerationJob,
    store: TimetableGenerationJobStore,
) -> None:
    """Run one generation job and record its terminal state."""

    store.mark_running(job.job_id)
    try:
        timetable_id = generate_timetable(job.semester_id)
    except Exception:
        logger.exception(
            "Timetable generation failed for job_id=%s semester_id=%s",
            job.job_id,
            job.semester_id,
            extra={"job_id": job.job_id, "semester_id": job.semester_id},
        )
        store.mark_failed(job.job_id, "Timetable generation failed")
        return

    store.mark_completed(job.job_id, timetable_id)


def _start_generation(
    semester_id: int,
    background_tasks: BackgroundTasks,
    store: TimetableGenerationJobStore,
) -> TimetableGenerationJobResponse:
    try:
        job = store.create_job(semester_id)
    except ActiveGenerationJobExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    background_tasks.add_task(run_timetable_generation_job, job, store)
    return TimetableGenerationJobResponse.from_job(job)


@router.post(
    "/semesters/{semester_id}/generate",
    response_model=TimetableGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_timetable_generation(
    background_tasks: BackgroundTasks,
    semester_id: int = Path(gt=0),
    store: TimetableGenerationJobStore = Depends(get_job_store),
) -> TimetableGenerationJobResponse:
    return _start_generation(semester_id, background_tasks, store)


@router.get(
    "/jobs/{job_id}",
    response_model=TimetableGenerationJobResponse,
)
def get_timetable_generation_job(
    job_id: str,
    store: TimetableGenerationJobStore = Depends(get_job_store),
) -> TimetableGenerationJobResponse:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail="Timetable-generation job not found"
        )
    return TimetableGenerationJobResponse.from_job(job)
