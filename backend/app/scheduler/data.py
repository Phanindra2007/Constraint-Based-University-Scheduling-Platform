from datetime import date, datetime, time, timedelta
from typing import Any, LiteralString

from psycopg.rows import dict_row

from app.database.connection import get_connection
from app.scheduler.config import (
    ANY_ROOM_TYPE,
    MAX_PREFERENCE_SCORE,
    MIN_PREFERENCE_SCORE,
    NUM_DAYS,
    PERIOD_DURATION_MINUTES,
    TEACHING_BLOCKS,
    TEACHING_BLOCK_START_TIMES,
)
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)
from app.scheduler.scoring import SchedulingFacultyPreference


def duration_minutes_to_periods(duration_minutes: int) -> int:
    """Convert a positive whole teaching-period duration to period indexes."""

    if duration_minutes <= 0 or duration_minutes % PERIOD_DURATION_MINUTES != 0:
        raise ValueError(
            f"duration_minutes must be a positive multiple of "
            f"{PERIOD_DURATION_MINUTES}, got {duration_minutes}."
        )
    return duration_minutes // PERIOD_DURATION_MINUTES


def time_range_to_periods(start_time: time, end_time: time) -> set[int]:
    """Return periods whose complete teaching intervals fit in a time range."""

    if start_time >= end_time:
        raise ValueError(
            f"Availability start time {start_time} must be before end time "
            f"{end_time}."
        )

    available_periods: set[int] = set()
    period_duration = timedelta(minutes=PERIOD_DURATION_MINUTES)

    for block, block_start_time in zip(
        TEACHING_BLOCKS,
        TEACHING_BLOCK_START_TIMES,
        strict=True,
    ):
        block_start = datetime.combine(date.min, block_start_time)
        for period_offset, period in enumerate(block):
            period_start = block_start + period_offset * period_duration
            period_end = period_start + period_duration
            window_start = datetime.combine(date.min, start_time)
            window_end = datetime.combine(date.min, end_time)
            if window_start <= period_start and period_end <= window_end:
                available_periods.add(period)

    return available_periods


# LiteralString tells type checkers that this parameter should contain
# SQL written directly in the source code, not dynamically constructed SQL.
# Query values still use %s placeholders and are passed separately through
# `params` so user/data values are safely parameterized.
def _fetch_all(
    query: LiteralString,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """Execute a read-only parameterized query using the shared connection pool."""

    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def load_scheduling_sessions(semester_id: int) -> list[SchedulingSession]:
    """Load semester offerings and expand each into its weekly sessions."""

    rows = _fetch_all(
        """
        SELECT
            co.id AS offering_id,
            co.course_id,
            co.faculty_id,
            co.batch_id,
            c.duration_minutes,
            c.sessions_per_week,
            c.required_room_type,
            c.min_capacity,
            b.student_count
        FROM course_offerings AS co
        JOIN courses AS c ON c.id = co.course_id
        JOIN batches AS b ON b.id = co.batch_id
        WHERE co.semester_id = %s
        ORDER BY co.id
        """,
        (semester_id,),
    )

    sessions: list[SchedulingSession] = []
    for row in rows:
        duration_periods = duration_minutes_to_periods(row["duration_minutes"])
        student_count = max(row["student_count"], row["min_capacity"] or 0)
        required_room_type = row["required_room_type"] or ANY_ROOM_TYPE

        for session_number in range(1, row["sessions_per_week"] + 1):
            sessions.append(
                SchedulingSession(
                    offering_id=row["offering_id"],
                    session_number=session_number,
                    course_id=row["course_id"],
                    faculty_id=row["faculty_id"],
                    batch_id=row["batch_id"],
                    duration_periods=duration_periods,
                    student_count=student_count,
                    required_room_type=required_room_type,
                )
            )

    return sessions


def load_rooms() -> list[SchedulingRoom]:
    """Load all rooms as scheduler room models."""

    rows = _fetch_all("""
        SELECT id, capacity, room_type
        FROM rooms
        ORDER BY id
        """)
    return [
        SchedulingRoom(
            id=row["id"],
            capacity=row["capacity"],
            room_type=row["room_type"],
        )
        for row in rows
    ]


def load_faculty_availability(
    semester_id: int,
) -> list[SchedulingFacultyAvailability]:
    """Load and convert semester-scoped faculty availability windows."""

    rows = _fetch_all(
        """
        SELECT faculty_id, day_of_week, start_time, end_time
        FROM faculty_availability
        WHERE semester_id = %s
          AND day_of_week BETWEEN 1 AND %s
        ORDER BY faculty_id, day_of_week, start_time
        """,
        (semester_id, NUM_DAYS),
    )
    return [
        SchedulingFacultyAvailability(
            faculty_id=row["faculty_id"],
            day=row["day_of_week"] - 1,
            available_periods=time_range_to_periods(row["start_time"], row["end_time"]),
        )
        for row in rows
    ]


def load_room_availability(semester_id: int) -> list[SchedulingRoomAvailability]:
    """Load and convert semester-scoped room availability windows."""

    rows = _fetch_all(
        """
        SELECT room_id, day_of_week, start_time, end_time
        FROM room_availability
        WHERE semester_id = %s
          AND day_of_week BETWEEN 1 AND %s
        ORDER BY room_id, day_of_week, start_time
        """,
        (semester_id, NUM_DAYS),
    )
    return [
        SchedulingRoomAvailability(
            room_id=row["room_id"],
            day=row["day_of_week"] - 1,
            available_periods=time_range_to_periods(row["start_time"], row["end_time"]),
        )
        for row in rows
    ]


def load_faculty_preferences(
    semester_id: int,
) -> list[SchedulingFacultyPreference]:
    """Load and convert semester-scoped faculty preference windows."""

    rows = _fetch_all(
        """
        SELECT faculty_id, day_of_week, start_time, end_time, preference_score
        FROM faculty_preferences
        WHERE semester_id = %s
          AND day_of_week BETWEEN 1 AND %s
        ORDER BY faculty_id, day_of_week, start_time
        """,
        (semester_id, NUM_DAYS),
    )

    preferences: list[SchedulingFacultyPreference] = []
    for row in rows:
        preference_score = row["preference_score"]
        if not MIN_PREFERENCE_SCORE <= preference_score <= MAX_PREFERENCE_SCORE:
            raise ValueError(
                "Faculty preference score must be between "
                f"{MIN_PREFERENCE_SCORE} and {MAX_PREFERENCE_SCORE}, got "
                f"{preference_score} for faculty_id={row['faculty_id']}."
            )

        preferred_periods = time_range_to_periods(row["start_time"], row["end_time"])
        if not preferred_periods:
            raise ValueError(
                "Faculty preference window has no matching teaching periods: "
                f"faculty_id={row['faculty_id']}, "
                f"day_of_week={row['day_of_week']}, "
                f"start_time={row['start_time']}, end_time={row['end_time']}."
            )

        preferences.append(
            SchedulingFacultyPreference(
                faculty_id=row["faculty_id"],
                day=row["day_of_week"] - 1,
                preferred_periods=preferred_periods,
                preference_score=preference_score,
            )
        )

    return preferences


def load_scheduler_data(
    semester_id: int,
) -> tuple[
    list[SchedulingSession],
    list[SchedulingRoom],
    list[SchedulingFacultyAvailability],
    list[SchedulingRoomAvailability],
    list[SchedulingFacultyPreference],
]:
    """Load all scheduler inputs for one semester."""

    return (
        load_scheduling_sessions(semester_id),
        load_rooms(),
        load_faculty_availability(semester_id),
        load_room_availability(semester_id),
        load_faculty_preferences(semester_id),
    )
