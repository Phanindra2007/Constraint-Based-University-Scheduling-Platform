from typing import Sequence

from ortools.sat.python import cp_model

from app.scheduler.model import build_scheduling_model
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)
from app.scheduler.variables import SessionVariables


def _extract_session_result(
    solver: cp_model.CpSolver,
    session: SchedulingSession,
    session_variables: SessionVariables,
) -> dict:
    """Extract the selected placement for one scheduled session."""

    # Exactly-one constraints guarantee that one placement is selected.
    for placement in session_variables.placements:
        if solver.Value(placement.presence):
            return {
                "offering_id": session.offering_id,
                "session_number": session.session_number,
                "course_id": session.course_id,
                "faculty_id": session.faculty_id,
                "batch_id": session.batch_id,
                "day": placement.day,
                "start_period": placement.start_period,
                "room_id": placement.room_id,
                "duration_periods": session.duration_periods,
            }

    raise RuntimeError(
        "The solver returned a solution without a selected placement "
        f"for offering {session.offering_id}, session {session.session_number}."
    )


def solve_schedule(
    sessions: Sequence[SchedulingSession],
    num_days: int,
    num_periods: int,
    rooms: list[SchedulingRoom],
    faculty_availability: list[SchedulingFacultyAvailability],
    room_availability: list[SchedulingRoomAvailability],
) -> list[dict]:
    """Solve the current hard-constraint model using the supplied rooms."""

    model, session_variables = build_scheduling_model(
        sessions,
        num_days,
        num_periods,
        rooms,
        faculty_availability,
        room_availability,
    )
    solver = cp_model.CpSolver()

    # Solve the CP-SAT model using the current hard constraints.
    status = solver.Solve(model)

    # Check the solver result before attempting to extract placements.
    if status == cp_model.INFEASIBLE:
        raise ValueError("No timetable satisfies the current hard constraints.")
    if status in (cp_model.UNKNOWN, cp_model.MODEL_INVALID):
        raise RuntimeError(
            "The CP-SAT solver could not produce a valid scheduling result."
        )
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Unexpected CP-SAT solver status: {status}.")

    # Extract the one selected placement for each session in input order.
    return [
        _extract_session_result(solver, session, variables)
        for session, variables in zip(sessions, session_variables)
    ]
