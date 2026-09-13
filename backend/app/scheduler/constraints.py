from collections import defaultdict
from typing import Sequence

from ortools.sat.python import cp_model

from app.scheduler.models import SchedulingSession
from app.scheduler.variables import SessionVariables


def add_exactly_one_placement_constraints(
    model: cp_model.CpModel,
    session_variables: Sequence[SessionVariables],
) -> None:
    """Require every session to select exactly one placement."""

    for variables in session_variables:
        # A session must be assigned to one concrete day, period, and room.
        model.add_exactly_one(
            [placement.presence for placement in variables.placements]
        )


def add_faculty_no_overlap_constraints(
    model: cp_model.CpModel,
    sessions: Sequence[SchedulingSession],
    session_variables: Sequence[SessionVariables],
) -> None:
    """Prevent a faculty member from teaching overlapping sessions on a day."""

    intervals_by_faculty_and_day: defaultdict[
        tuple[int, int], list[cp_model.IntervalVar]
    ] = defaultdict(list)

    for session, variables in zip(sessions, session_variables):
        for placement in variables.placements:
            intervals_by_faculty_and_day[(placement.day, session.faculty_id)].append(
                placement.interval
            )

    # Each day/faculty group is independent from every other day/faculty group.
    for intervals in intervals_by_faculty_and_day.values():
        model.add_no_overlap(intervals)


def add_batch_no_overlap_constraints(
    model: cp_model.CpModel,
    sessions: Sequence[SchedulingSession],
    session_variables: Sequence[SessionVariables],
) -> None:
    """Prevent a batch from having overlapping sessions on a day."""

    intervals_by_batch_and_day: defaultdict[
        tuple[int, int], list[cp_model.IntervalVar]
    ] = defaultdict(list)

    for session, variables in zip(sessions, session_variables):
        for placement in variables.placements:
            intervals_by_batch_and_day[(placement.day, session.batch_id)].append(
                placement.interval
            )

    # Each day/batch group gets its own no-overlap constraint.
    for intervals in intervals_by_batch_and_day.values():
        model.add_no_overlap(intervals)


def add_room_no_overlap_constraints(
    model: cp_model.CpModel,
    session_variables: Sequence[SessionVariables],
) -> None:
    """Prevent a room from hosting overlapping sessions on a day."""

    intervals_by_room_and_day: defaultdict[
        tuple[int, int], list[cp_model.IntervalVar]
    ] = defaultdict(list)

    for variables in session_variables:
        for placement in variables.placements:
            intervals_by_room_and_day[(placement.day, placement.room_id)].append(
                placement.interval
            )

    # Each day/room group gets its own no-overlap constraint.
    for intervals in intervals_by_room_and_day.values():
        model.add_no_overlap(intervals)


def add_hard_constraints(
    model: cp_model.CpModel,
    sessions: Sequence[SchedulingSession],
    session_variables: Sequence[SessionVariables],
) -> None:
    """Add the initial hard constraints for all scheduling sessions."""

    add_exactly_one_placement_constraints(model, session_variables)
    add_faculty_no_overlap_constraints(model, sessions, session_variables)
    add_batch_no_overlap_constraints(model, sessions, session_variables)
    add_room_no_overlap_constraints(model, session_variables)
