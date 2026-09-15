from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, status

from app.scheduler.jobs import TimetableGenerationJob, job_store
from app.scheduler.service import generate_timetable
from app.schemas.jobs import TimetableGenerationJobResponse

router = APIRouter(prefix="/api", tags=["Timetable generation"])


def run_timetable_generation_job(job: TimetableGenerationJob) -> None:
    """Run one generation job and record its terminal state."""

    job_store.mark_running(job.job_id)
    try:
        timetable_id = generate_timetable(job.semester_id)
    except Exception as error:
        error_message = str(error) or error.__class__.__name__
        job_store.mark_failed(job.job_id, error_message)
        return

    job_store.mark_completed(job.job_id, timetable_id)


def _start_generation(
    semester_id: int,
    background_tasks: BackgroundTasks,
) -> TimetableGenerationJobResponse:
    job = job_store.create_job(semester_id)
    background_tasks.add_task(run_timetable_generation_job, job)
    return TimetableGenerationJobResponse.from_job(job)


@router.post(
    "/semesters/{semester_id}/generate",
    response_model=TimetableGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_timetable_generation(
    background_tasks: BackgroundTasks,
    semester_id: int = Path(gt=0),
) -> TimetableGenerationJobResponse:
    return _start_generation(semester_id, background_tasks)


@router.get(
    "/jobs/{job_id}",
    response_model=TimetableGenerationJobResponse,
)
def get_timetable_generation_job(job_id: str) -> TimetableGenerationJobResponse:
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail="Timetable-generation job not found"
        )
    return TimetableGenerationJobResponse.from_job(job)
