from app.scheduler.config import NUM_DAYS, NUM_PERIODS
from app.scheduler.data import load_scheduler_data
from app.scheduler.persistence import save_timetable
from app.scheduler.solver import solve_schedule
from app.scheduler.validation import validate_schedule


def generate_timetable(semester_id: int) -> int:
    """Generate and persist a timetable for one semester."""

    (
        sessions,
        rooms,
        faculty_availability,
        room_availability,
        faculty_preferences,
    ) = load_scheduler_data(semester_id)

    result = solve_schedule(
        sessions=sessions,
        num_days=NUM_DAYS,
        num_periods=NUM_PERIODS,
        rooms=rooms,
        faculty_availability=faculty_availability,
        room_availability=room_availability,
        faculty_preferences=faculty_preferences,
    )
    placements = result.placements
    validate_schedule(
        sessions=sessions,
        rooms=rooms,
        faculty_availability=faculty_availability,
        room_availability=room_availability,
        placements=placements,
    )

    return save_timetable(semester_id, placements, result.score.total_penalty)
