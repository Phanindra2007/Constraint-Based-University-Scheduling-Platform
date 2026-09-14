from dataclasses import dataclass
from collections.abc import Sequence

from app.scheduler.config import MAX_PREFERENCE_SCORE, TEACHING_BLOCKS
from app.scheduler.models import SchedulingRoom, SchedulingSession


@dataclass
class SchedulingFacultyPreference:
    """A faculty preference window represented by scheduler period indexes."""

    faculty_id: int
    day: int
    preferred_periods: set[int]
    preference_score: int


@dataclass
class ScheduleScore:
    """Penalty components for a scheduled timetable."""

    batch_gap_penalty: int
    faculty_idle_penalty: int
    faculty_preference_penalty: int
    room_waste_penalty: int
    total_penalty: int


@dataclass
class ScheduleResult:
    """The selected placements and their scoring result."""

    placements: list[dict]
    score: ScheduleScore


def calculate_faculty_preference_penalty(
    sessions: Sequence[SchedulingSession],
    placements: Sequence[dict],
    preferences: Sequence[SchedulingFacultyPreference],
) -> int:
    """Calculate the faculty preference penalty for selected placements."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    scores_by_faculty_day_period: dict[tuple[int, int, int], int] = {}
    for preference in preferences:
        for period in preference.preferred_periods:
            key = (preference.faculty_id, preference.day, period)
            existing_score = scores_by_faculty_day_period.get(key)
            scores_by_faculty_day_period[key] = (
                preference.preference_score
                if existing_score is None
                else max(existing_score, preference.preference_score)
            )

    penalty = 0
    for placement in placements:
        session_key = (placement["offering_id"], placement["session_number"])
        try:
            session = sessions_by_key[session_key]
        except KeyError as error:
            raise ValueError(
                "Placement does not match a scheduling session: "
                f"offering_id={session_key[0]}, session_number={session_key[1]}."
            ) from error

        day = placement["day"]
        start_period = placement["start_period"]
        occupied_periods = range(
            start_period,
            start_period + session.duration_periods,
        )
        for period in occupied_periods:
            matched_score = scores_by_faculty_day_period.get(
                (session.faculty_id, day, period)
            )
            if matched_score is not None:
                penalty += MAX_PREFERENCE_SCORE - matched_score

    return penalty


def calculate_room_waste_penalty(
    sessions: Sequence[SchedulingSession],
    rooms: Sequence[SchedulingRoom],
    placements: Sequence[dict],
) -> int:
    """Calculate unused room capacity once for each selected session."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    rooms_by_id = {room.id: room for room in rooms}

    penalty = 0
    for placement in placements:
        session_key = (placement["offering_id"], placement["session_number"])
        try:
            session = sessions_by_key[session_key]
        except KeyError as error:
            raise ValueError(
                "Placement does not match a scheduling session: "
                f"offering_id={session_key[0]}, session_number={session_key[1]}."
            ) from error

        room_id = placement["room_id"]
        try:
            room = rooms_by_id[room_id]
        except KeyError as error:
            raise ValueError(
                f"Placement references unknown room_id={room_id}."
            ) from error

        room_waste = room.capacity - session.student_count
        if room_waste < 0:
            raise ValueError(
                "Room capacity is below session student count: "
                f"room_id={room.id}, capacity={room.capacity}, "
                f"student_count={session.student_count}, "
                f"offering_id={session.offering_id}, "
                f"session_number={session.session_number}."
            )
        penalty += room_waste

    return penalty


def calculate_batch_gap_penalty(
    sessions: Sequence[SchedulingSession],
    placements: Sequence[dict],
) -> int:
    """Calculate gaps between sessions within each batch, day, and block."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    sessions_by_batch_day_block: dict[tuple[int, int, int], list[tuple[int, int]]] = {}

    for placement in placements:
        session_key = (placement["offering_id"], placement["session_number"])
        try:
            session = sessions_by_key[session_key]
        except KeyError as error:
            raise ValueError(
                "Placement does not match a scheduling session: "
                f"offering_id={session_key[0]}, session_number={session_key[1]}."
            ) from error

        start_period = placement["start_period"]
        end_period = start_period + session.duration_periods
        containing_block_index = next(
            (
                block_index
                for block_index, block in enumerate(TEACHING_BLOCKS)
                if set(range(start_period, end_period)) <= set(block)
            ),
            None,
        )
        if containing_block_index is None:
            raise ValueError(
                "Session placement does not fit within a teaching block: "
                f"offering_id={session.offering_id}, "
                f"session_number={session.session_number}, "
                f"start_period={start_period}, "
                f"duration_periods={session.duration_periods}."
            )

        group_key = (session.batch_id, placement["day"], containing_block_index)
        sessions_by_batch_day_block.setdefault(group_key, []).append(
            (start_period, end_period)
        )

    penalty = 0
    for scheduled_sessions in sessions_by_batch_day_block.values():
        scheduled_sessions.sort()
        for (_, previous_end), (next_start, _) in zip(
            scheduled_sessions, scheduled_sessions[1:], strict=False
        ):
            gap = next_start - previous_end
            if gap < 0:
                raise ValueError(
                    "Batch sessions overlap and produce a negative gap: "
                    f"previous_end={previous_end}, next_start={next_start}."
                )
            penalty += gap

    return penalty


def calculate_faculty_idle_penalty(
    sessions: Sequence[SchedulingSession],
    placements: Sequence[dict],
) -> int:
    """Calculate idle time between sessions for each faculty member."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    sessions_by_faculty_day_block: dict[tuple[int, int, int], list[tuple[int, int]]] = (
        {}
    )

    for placement in placements:
        session_key = (placement["offering_id"], placement["session_number"])
        try:
            session = sessions_by_key[session_key]
        except KeyError as error:
            raise ValueError(
                "Placement does not match a scheduling session: "
                f"offering_id={session_key[0]}, session_number={session_key[1]}."
            ) from error

        start_period = placement["start_period"]
        end_period = start_period + session.duration_periods
        containing_block_index = next(
            (
                block_index
                for block_index, block in enumerate(TEACHING_BLOCKS)
                if set(range(start_period, end_period)) <= set(block)
            ),
            None,
        )
        if containing_block_index is None:
            raise ValueError(
                "Session placement does not fit within a teaching block: "
                f"offering_id={session.offering_id}, "
                f"session_number={session.session_number}, "
                f"start_period={start_period}, "
                f"duration_periods={session.duration_periods}."
            )

        group_key = (
            session.faculty_id,
            placement["day"],
            containing_block_index,
        )
        sessions_by_faculty_day_block.setdefault(group_key, []).append(
            (start_period, end_period)
        )

    penalty = 0
    for scheduled_sessions in sessions_by_faculty_day_block.values():
        scheduled_sessions.sort()
        for (_, previous_end), (next_start, _) in zip(
            scheduled_sessions, scheduled_sessions[1:], strict=False
        ):
            idle = next_start - previous_end
            if idle < 0:
                raise ValueError(
                    "Faculty sessions overlap and produce a negative idle time: "
                    f"previous_end={previous_end}, next_start={next_start}."
                )
            penalty += idle

    return penalty
