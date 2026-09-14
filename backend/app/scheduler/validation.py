from collections import defaultdict
from collections.abc import Sequence

from app.scheduler.config import ANY_ROOM_TYPE, NUM_DAYS, NUM_PERIODS, TEACHING_BLOCKS
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)


def _placement_key(placement: dict) -> tuple[int, int]:
    try:
        return placement["offering_id"], placement["session_number"]
    except KeyError as error:
        raise ValueError(
            f"Placement is missing required field: {error.args[0]}"
        ) from error


def _session_label(session: SchedulingSession) -> str:
    return f"offering {session.offering_id}, session {session.session_number}"


def _occupied_periods(placement: dict) -> set[int]:
    try:
        start_period = placement["start_period"]
        duration_periods = placement["duration_periods"]
    except KeyError as error:
        raise ValueError(
            f"Placement is missing required field: {error.args[0]}"
        ) from error

    if not isinstance(start_period, int) or not isinstance(duration_periods, int):
        raise ValueError(
            "Placement start_period and duration_periods must be integers."
        )
    if duration_periods <= 0:
        raise ValueError("Placement duration_periods must be positive.")

    return set(range(start_period, start_period + duration_periods))


def _find_availability_periods(
    availability: (
        Sequence[SchedulingFacultyAvailability] | Sequence[SchedulingRoomAvailability]
    ),
    resource_id: int,
    day: int,
) -> set[int]:
    periods: set[int] = set()
    for entry in availability:
        entry_resource_id = (
            entry.faculty_id
            if isinstance(entry, SchedulingFacultyAvailability)
            else entry.room_id
        )
        if entry_resource_id == resource_id and entry.day == day:
            periods.update(entry.available_periods)
    return periods


def _validate_block_containment(
    occupied_periods: set[int],
    session: SchedulingSession,
) -> None:
    if not any(occupied_periods <= set(block) for block in TEACHING_BLOCKS):
        raise ValueError(
            f"{_session_label(session)} crosses a teaching-block boundary."
        )


def _validate_no_overlap(
    placements: Sequence[dict],
    sessions_by_key: dict[tuple[int, int], SchedulingSession],
    resource_name: str,
) -> None:
    groups: defaultdict[tuple[int, int], list[tuple[dict, set[int]]]] = defaultdict(
        list
    )

    for placement in placements:
        session = sessions_by_key[_placement_key(placement)]
        try:
            resource_id = placement[resource_name]
        except KeyError as error:
            raise ValueError(
                f"Placement is missing required field: {error.args[0]}"
            ) from error
        groups[(placement["day"], resource_id)].append(
            (placement, _occupied_periods(placement))
        )

    for group in groups.values():
        for index, (first, first_periods) in enumerate(group):
            for second, second_periods in group[index + 1 :]:
                if first_periods.isdisjoint(second_periods):
                    continue
                raise ValueError(
                    f"Overlapping sessions for {resource_name} "
                    f"{first[resource_name]} on day {first['day']}: "
                    f"{_placement_key(first)} and {_placement_key(second)}."
                )


def validate_schedule(
    sessions: Sequence[SchedulingSession],
    rooms: Sequence[SchedulingRoom],
    faculty_availability: Sequence[SchedulingFacultyAvailability],
    room_availability: Sequence[SchedulingRoomAvailability],
    placements: Sequence[dict],
) -> None:
    """Validate generated placements against scheduler inputs and hard rules."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    if len(sessions_by_key) != len(sessions):
        raise ValueError("Scheduling sessions contain duplicate identities.")

    placements_by_key: dict[tuple[int, int], dict] = {}
    for placement in placements:
        key = _placement_key(placement)
        if key not in sessions_by_key:
            raise ValueError(f"Unexpected placement for offering/session {key}.")
        if key in placements_by_key:
            raise ValueError(f"Duplicate placement for offering/session {key}.")
        placements_by_key[key] = placement

    missing_keys = set(sessions_by_key) - set(placements_by_key)
    if missing_keys:
        raise ValueError(
            f"Missing placement for offering/session {sorted(missing_keys)[0]}."
        )

    rooms_by_id = {room.id: room for room in rooms}
    if len(rooms_by_id) != len(rooms):
        raise ValueError("Scheduling rooms contain duplicate IDs.")

    for key, placement in placements_by_key.items():
        session = sessions_by_key[key]
        try:
            day = placement["day"]
            room_id = placement["room_id"]
        except KeyError as error:
            raise ValueError(
                f"Placement is missing required field: {error.args[0]}"
            ) from error

        if not isinstance(day, int) or not 0 <= day < NUM_DAYS:
            raise ValueError(f"Invalid day {day} for {_session_label(session)}.")

        occupied_periods = _occupied_periods(placement)
        if placement["duration_periods"] != session.duration_periods:
            raise ValueError(
                f"Duration mismatch for {_session_label(session)}: "
                f"expected {session.duration_periods}, "
                f"got {placement['duration_periods']}."
            )
        if (
            not occupied_periods
            or min(occupied_periods) < 0
            or max(occupied_periods) >= NUM_PERIODS
        ):
            raise ValueError(f"Invalid period range for {_session_label(session)}.")

        _validate_block_containment(occupied_periods, session)

        room = rooms_by_id.get(room_id)
        if room is None:
            raise ValueError(f"Unknown room {room_id} for {_session_label(session)}.")
        if room.capacity < session.student_count:
            raise ValueError(
                f"Room {room_id} is too small for {_session_label(session)}."
            )
        if (
            session.required_room_type != ANY_ROOM_TYPE
            and room.room_type != session.required_room_type
        ):
            raise ValueError(
                f"Room {room_id} has type {room.room_type}, but "
                f"{_session_label(session)} requires {session.required_room_type}."
            )

        faculty_periods = _find_availability_periods(
            faculty_availability,
            session.faculty_id,
            day,
        )
        if not occupied_periods <= faculty_periods:
            raise ValueError(
                f"Faculty {session.faculty_id} is unavailable for "
                f"{_session_label(session)}."
            )

        room_periods = _find_availability_periods(room_availability, room_id, day)
        if not occupied_periods <= room_periods:
            raise ValueError(
                f"Room {room_id} is unavailable for {_session_label(session)}."
            )

    _validate_no_overlap(placements, sessions_by_key, "faculty_id")
    _validate_no_overlap(placements, sessions_by_key, "batch_id")
    _validate_no_overlap(placements, sessions_by_key, "room_id")
