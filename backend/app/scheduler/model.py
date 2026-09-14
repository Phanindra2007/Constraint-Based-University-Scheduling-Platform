from typing import Sequence

from ortools.sat.python import cp_model

from app.scheduler import config
from app.scheduler.constraints import add_hard_constraints
from app.scheduler.config import TEACHING_BLOCKS
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)
from app.scheduler.scoring import (
    SchedulingFacultyPreference,
    calculate_placement_objective_cost,
)
from app.scheduler.variables import (
    PlacementVariables,
    SessionVariables,
    create_session_variables,
)


def _teaching_block_index(
    placement: PlacementVariables,
    session: SchedulingSession,
) -> int:
    occupied_periods = set(
        range(placement.start_period, placement.start_period + session.duration_periods)
    )
    for block_index, block in enumerate(TEACHING_BLOCKS):
        if occupied_periods <= set(block):
            return block_index
    raise ValueError(
        "Session placement does not fit within a teaching block: "
        f"offering_id={session.offering_id}, "
        f"session_number={session.session_number}, "
        f"start_period={placement.start_period}, "
        f"duration_periods={session.duration_periods}."
    )


def _add_consecutive_gap_terms(
    model: cp_model.CpModel,
    sessions: Sequence[SchedulingSession],
    session_variables: Sequence[SessionVariables],
    resource_ids: Sequence[int],
    weight: int,
    objective_name: str,
) -> list[cp_model.LinearExpr]:
    placements_by_resource_day_block: dict[
        tuple[int, int, int], list[tuple[int, PlacementVariables]]
    ] = {}
    for session_index, (session, variables) in enumerate(
        zip(sessions, session_variables, strict=True)
    ):
        for placement in variables.placements:
            group_key = (
                resource_ids[session_index],
                placement.day,
                _teaching_block_index(placement, session),
            )
            placements_by_resource_day_block.setdefault(group_key, []).append(
                (session_index, placement)
            )

    objective_terms: list[cp_model.LinearExpr] = []
    for group_key, scheduled_placements in placements_by_resource_day_block.items():
        scheduled_placements.sort(key=lambda item: item[1].start_period)
        for first_index, (first_session_index, first) in enumerate(
            scheduled_placements
        ):
            first_session = sessions[first_session_index]
            first_end = first.start_period + first_session.duration_periods
            for second_session_index, second in scheduled_placements[first_index + 1 :]:
                if first_session_index == second_session_index:
                    continue

                second_session = sessions[second_session_index]
                if first_end > second.start_period:
                    continue

                gap = second.start_period - first_end
                middle_literals = [
                    candidate.presence
                    for candidate_session_index, candidate in scheduled_placements
                    if candidate_session_index
                    not in {
                        first_session_index,
                        second_session_index,
                    }
                    and candidate.start_period >= first_end
                    and candidate.start_period
                    + sessions[candidate_session_index].duration_periods
                    <= second.start_period
                ]
                adjacency = model.new_bool_var(
                    f"{objective_name}_adjacent_"
                    f"{group_key[0]}_day_{group_key[1]}_block_{group_key[2]}_"
                    f"{first_session_index}_{second_session_index}_"
                    f"{first.start_period}_{second.start_period}"
                )
                required_literals = [
                    first.presence,
                    second.presence,
                    *(literal.Not() for literal in middle_literals),
                ]
                model.add_bool_and(required_literals).only_enforce_if(adjacency)
                model.add_bool_or(
                    [literal.Not() for literal in required_literals] + [adjacency]
                )
                objective_terms.append(adjacency * gap * weight)

    return objective_terms


def build_scheduling_model(
    sessions: Sequence[SchedulingSession],
    num_days: int,
    num_periods: int,
    rooms: list[SchedulingRoom],
    faculty_availability: list[SchedulingFacultyAvailability],
    room_availability: list[SchedulingRoomAvailability],
    faculty_preferences: list[SchedulingFacultyPreference],
) -> tuple[cp_model.CpModel, list[SessionVariables]]:
    """Assemble a CP-SAT model from sessions, rooms, variables, and hard constraints."""

    model = cp_model.CpModel()
    session_variables = [
        create_session_variables(
            model,
            session,
            num_days,
            num_periods,
            rooms,
            faculty_availability,
            room_availability,
        )
        for session in sessions
    ]

    add_hard_constraints(model, sessions, session_variables)

    rooms_by_id = {room.id: room for room in rooms}
    objective_terms: list[cp_model.LinearExpr] = []
    for session, variables in zip(sessions, session_variables):
        for placement in variables.placements:
            room = rooms_by_id[placement.room_id]
            placement_cost = calculate_placement_objective_cost(
                session,
                room,
                placement,
                faculty_preferences,
            )
            objective_terms.append(placement.presence * placement_cost)

    objective_terms.extend(
        _add_consecutive_gap_terms(
            model,
            sessions,
            session_variables,
            [session.batch_id for session in sessions],
            config.BATCH_GAP_WEIGHT,
            "batch_gap",
        )
    )
    objective_terms.extend(
        _add_consecutive_gap_terms(
            model,
            sessions,
            session_variables,
            [session.faculty_id for session in sessions],
            config.FACULTY_IDLE_WEIGHT,
            "faculty_idle",
        )
    )

    model.minimize(sum(objective_terms))

    return model, session_variables
