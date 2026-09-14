from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.scheduler.config import TEACHING_BLOCKS
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)


@dataclass
class PlacementVariables:
    """CP-SAT variables for one concrete session placement."""

    day: int
    start_period: int
    room_id: int
    presence: cp_model.IntVar
    interval: cp_model.IntervalVar


@dataclass
class SessionVariables:
    """
    Stores the placement variables associated with one scheduling session.
    """

    placements: list[PlacementVariables]


def is_period_range_available(
    available_periods: set[int],
    start_period: int,
    duration_periods: int,
) -> bool:
    """Return whether every period occupied by a session is available."""

    occupied_periods = range(start_period, start_period + duration_periods)
    return all(period in available_periods for period in occupied_periods)


def create_session_variables(
    model: cp_model.CpModel,
    session: SchedulingSession,
    num_days: int,
    num_periods: int,
    rooms: list[SchedulingRoom],
    faculty_availability: list[SchedulingFacultyAvailability],
    room_availability: list[SchedulingRoomAvailability],
) -> SessionVariables:
    """
    Create the decision variables for one scheduling session.
    """

    suitable_rooms = [
        room
        for room in rooms
        if room.capacity >= session.student_count
        and room.room_type == session.required_room_type
    ]
    if not suitable_rooms:
        raise ValueError(
            "No suitable room exists for offering "
            f"{session.offering_id}, session {session.session_number}: "
            f"requires capacity >= {session.student_count} and room type "
            f"{session.required_room_type}."
        )

    placements = []

    for day in range(num_days):
        faculty_periods = set()

        for availability in faculty_availability:
            if (
                availability.faculty_id == session.faculty_id
                and availability.day == day
            ):
                faculty_periods.update(availability.available_periods)

        # Teaching blocks prevent placement windows from crossing the break.
        for teaching_block in TEACHING_BLOCKS:
            for block_index in range(
                len(teaching_block) - session.duration_periods + 1
            ):
                start_period = teaching_block[block_index]
                for room in suitable_rooms:
                    room_periods = set()

                    for availability in room_availability:
                        if availability.room_id == room.id and availability.day == day:
                            room_periods.update(availability.available_periods)

                    if not is_period_range_available(
                        faculty_periods,
                        start_period,
                        session.duration_periods,
                    ) or not is_period_range_available(
                        room_periods,
                        start_period,
                        session.duration_periods,
                    ):
                        continue

                    # Each placement represents one possible (day, start_period, room) assignment.
                    placement_name = (
                        f"session_{session.offering_id}_{session.session_number}"
                        f"_day_{day}_start_{start_period}_room_{room.id}"
                    )
                    presence = model.new_bool_var(f"{placement_name}_present")

                    # Optional intervals let overlap constraints see only selected placements.
                    interval = model.new_optional_fixed_size_interval_var(
                        start_period,
                        session.duration_periods,
                        presence,
                        f"{placement_name}_interval",
                    )

                    placements.append(
                        PlacementVariables(
                            day=day,
                            start_period=start_period,
                            room_id=room.id,
                            presence=presence,
                            interval=interval,
                        )
                    )

    if not placements:
        raise ValueError(
            "No feasible placement exists for offering "
            f"{session.offering_id}, session {session.session_number} "
            "after applying room suitability and availability."
        )

    return SessionVariables(placements=placements)
