from datetime import date, datetime, time, timedelta

from app.database.connection import get_connection
from app.scheduler.config import (
    NUM_DAYS,
    PERIOD_DURATION_MINUTES,
    TEACHING_BLOCKS,
    TEACHING_BLOCK_START_TIMES,
)


def _period_range_to_times(
    start_period: int, duration_periods: int
) -> tuple[time, time]:
    """Convert a placement to clock times within one teaching block."""

    if duration_periods <= 0:
        raise ValueError("duration_periods must be positive.")

    occupied_periods = set(range(start_period, start_period + duration_periods))
    for block, block_start_time in zip(
        TEACHING_BLOCKS,
        TEACHING_BLOCK_START_TIMES,
        strict=True,
    ):
        if not occupied_periods <= set(block):
            continue

        block_start = datetime.combine(date.min, block_start_time)
        period_offset = block.index(start_period)
        period_duration = timedelta(minutes=PERIOD_DURATION_MINUTES)
        start_datetime = block_start + period_offset * period_duration
        end_datetime = start_datetime + duration_periods * period_duration
        return start_datetime.time(), end_datetime.time()

    raise ValueError(
        "Placement crosses a teaching-block boundary or uses an invalid "
        f"period range: start_period={start_period}, "
        f"duration_periods={duration_periods}."
    )


def save_timetable(semester_id: int, placements: list[dict], score: int) -> int:
    """Persist one generated timetable and all of its placements atomically."""

    with get_connection() as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(version_number), 0) + 1
                    FROM timetables
                    WHERE semester_id = %s
                    """,
                    (semester_id,),
                )
                version_row = cursor.fetchone()
                if version_row is None:
                    raise RuntimeError(
                        "Could not determine the next timetable version."
                    )
                version_number = version_row[0]

                cursor.execute(
                    """
                    INSERT INTO timetables
                        (semester_id, version_number, score, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (semester_id, version_number, score, "ACTIVE"),
                )
                timetable_row = cursor.fetchone()
                if timetable_row is None:
                    raise RuntimeError("Timetable insert did not return an id.")
                timetable_id = timetable_row[0]

                for placement in placements:
                    start_time, end_time = _period_range_to_times(
                        placement["start_period"],
                        placement["duration_periods"],
                    )
                    day = placement["day"]
                    if not 0 <= day < NUM_DAYS:
                        raise ValueError(f"Invalid scheduler day: {day}.")

                    cursor.execute(
                        """
                        INSERT INTO timetable_slots
                            (
                                timetable_id,
                                course_offering_id,
                                room_id,
                                day_of_week,
                                start_time,
                                end_time
                            )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            timetable_id,
                            placement["offering_id"],
                            placement["room_id"],
                            day + 1,
                            start_time,
                            end_time,
                        ),
                    )

                return timetable_id
